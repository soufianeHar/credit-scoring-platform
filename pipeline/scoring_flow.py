"""
scoring_flow.py

Pipeline d'orchestration du scoring crédit, construit avec Prefect.
Enchaîne automatiquement : chargement des données brutes -> nettoyage ->
feature engineering -> chargement du modèle -> génération des scores.

Réutilise scoring_lib.preprocessing et scoring_lib.features (Semaine 3),
et le modèle entraîné à la Semaine 4 (scoring_lib/model_lgbm.pkl),
sans dupliquer aucune logique.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import joblib
from prefect import task, flow

from scoring_lib.preprocessing import clean_pipeline
from scoring_lib.features import build_features


@task(name="Charger les données brutes")
def load_raw_data(filepath: str) -> pd.DataFrame:
    """Charge le CSV brut de clients à scorer."""
    df = pd.read_csv(filepath)
    print(f"Données chargées : {df.shape[0]} lignes, {df.shape[1]} colonnes")
    return df


@task(name="Nettoyer les données")
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Applique le pipeline de nettoyage déjà validé (Semaine 3)."""
    df_clean = clean_pipeline(df)
    print(f"Données nettoyées : {df_clean.shape[0]} lignes restantes")
    return df_clean


@task(name="Créer les features")
def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Applique le feature engineering déjà validé (Semaine 3)."""
    df_final = build_features(df)
    print(f"Features créées : {df_final.shape[1]} colonnes au total")
    return df_final


@task(name="Charger le modèle")
def load_model(model_path: str):
    """Charge le modèle LightGBM déjà entraîné (Semaine 4)."""
    model = joblib.load(model_path)
    print("Modèle chargé avec succès")
    return model


@task(name="Générer les scores")
def generate_scores(df: pd.DataFrame, model) -> pd.DataFrame:
    """Calcule le score de risque pour chaque client."""
    X = df.drop(columns=["customer_id", "target"], errors="ignore")
    scores = model.predict_proba(X)[:, 1]

    result = df[["customer_id"]].copy()
    result["risk_score"] = scores

    print(f"Scores générés pour {len(result)} clients")
    print(result.head())
    return result


@flow(name="Pipeline de scoring crédit")
def scoring_pipeline(
    data_path: str = "data/cs-training.csv",
    model_path: str = "scoring_lib/model_lgbm.pkl",
):
    """
    Flow principal : enchaîne toutes les étapes du pipeline de scoring.

    C'est le point d'entrée unique qui reproduit, de façon automatisée
    et traçable, exactement la logique validée manuellement dans les
    notebooks des Semaines 3 et 4.
    """
    raw_data = load_raw_data(data_path)
    cleaned_data = clean_data(raw_data)
    features_data = create_features(cleaned_data)
    model = load_model(model_path)
    scores = generate_scores(features_data, model)
    return scores


if __name__ == "__main__":
    scoring_pipeline.serve(
        name="scoring-pipeline-daily",
        interval=86400,  # toutes les 24h (86400 secondes) - simule un ré-entraînement/scoring quotidien
    )