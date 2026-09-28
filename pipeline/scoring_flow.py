"""
scoring_flow.py

Pipeline d'orchestration du scoring crédit, construit avec Prefect.
Enchaîne : chargement -> nettoyage -> features -> modèle -> scores -> BigQuery.
Réutilise scoring_lib (Semaines 3-4) sans dupliquer de logique.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import joblib
from google.cloud import bigquery
from prefect import task, flow

from scoring_lib.preprocessing import clean_pipeline
from scoring_lib.features import build_features

BQ_PROJECT = "credit-scoring-platform"
BQ_SCORES_TABLE = f"{BQ_PROJECT}.credit_scoring.client_scores"


@task(name="Charger les données brutes")
def load_raw_data(filepath: str) -> pd.DataFrame:
    """Charge le CSV brut de clients à scorer."""
    df = pd.read_csv(filepath)
    print(f"Données chargées : {df.shape[0]} lignes, {df.shape[1]} colonnes")
    return df


@task(name="Nettoyer les données")
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Applique le pipeline de nettoyage (Semaine 3)."""
    df_clean = clean_pipeline(df)
    print(f"Données nettoyées : {df_clean.shape[0]} lignes restantes")
    return df_clean


@task(name="Créer les features")
def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Applique le feature engineering (Semaine 3)."""
    df_final = build_features(df)
    print(f"Features créées : {df_final.shape[1]} colonnes au total")
    return df_final


@task(name="Charger le modèle")
def load_model(model_path: str):
    """Charge le modèle LightGBM entraîné (Semaine 4)."""
    model = joblib.load(model_path)
    print("Modèle chargé avec succès")
    return model


@task(name="Générer les scores")
def generate_scores(df: pd.DataFrame, model) -> pd.DataFrame:
    """
    Calcule le score de risque de chaque client.
    Retourne les caractéristiques du client + son score + l'horodatage,
    pour que la table finale soit exploitable par l'agent Talk-to-Data.
    """
    X = df.drop(columns=["customer_id", "target"], errors="ignore")

    result = df.copy()
    result["risk_score"] = model.predict_proba(X)[:, 1]
    result["scored_at"] = pd.Timestamp.now(tz="UTC")

    print(f"Scores générés pour {len(result)} clients")
    print(result[["customer_id", "age", "risk_score"]].head())
    return result


@task(name="Sauvegarder les scores dans BigQuery", retries=2, retry_delay_seconds=10)
def save_scores_to_bigquery(df: pd.DataFrame, table_id: str = BQ_SCORES_TABLE) -> int:
    """
    Écrit les scores dans BigQuery par chargement en lot (load job).
    WRITE_TRUNCATE remplace le contenu à chaque exécution : la table reflète
    toujours le dernier scoring, sans doublons.
    """
    client = bigquery.Client(project=BQ_PROJECT)
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # attend la fin du chargement

    n_rows = client.get_table(table_id).num_rows
    print(f"{n_rows} lignes écrites dans {table_id}")
    return n_rows


@flow(name="Pipeline de scoring crédit")
def scoring_pipeline(
    data_path: str = "data/cs-training.csv",
    model_path: str = "scoring_lib/model_lgbm.pkl",
):
    """Flow principal : du CSV brut à la table de scores dans BigQuery."""
    raw_data = load_raw_data(data_path)
    cleaned_data = clean_data(raw_data)
    features_data = create_features(cleaned_data)
    model = load_model(model_path)
    scores = generate_scores(features_data, model)
    save_scores_to_bigquery(scores)
    return scores


if __name__ == "__main__":
    scoring_pipeline.serve(
        name="scoring-pipeline-daily",
        interval=86400,  # toutes les 24h
    )