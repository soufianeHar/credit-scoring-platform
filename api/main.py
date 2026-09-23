"""
main.py

API de scoring crédit en temps réel.
Reçoit les données d'un client via une requête HTTP, applique le même
pipeline de nettoyage/feature engineering que le batch (Semaines 3-5),
et retourne un score de risque instantané.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import joblib
from fastapi import FastAPI
from pydantic import BaseModel

from scoring_lib.preprocessing import clean_pipeline
from scoring_lib.features import build_features

app = FastAPI(title="Credit Scoring API", version="0.1.0")

# Chargement du modèle une seule fois, au démarrage de l'API
# (pas à chaque requête, ce qui serait lent et inutile)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "scoring_lib", "model_lgbm.pkl")
model = joblib.load(MODEL_PATH)


class ClientData(BaseModel):
    """
    Structure attendue en entrée de l'API : les données brutes d'un client,
    avec les mêmes noms de colonnes que le CSV original (avant renommage).
    """
    age: int
    RevolvingUtilizationOfUnsecuredLines: float
    NumberOfTime30_59DaysPastDueNotWorse: int = None
    DebtRatio: float
    MonthlyIncome: float = None
    NumberOfOpenCreditLinesAndLoans: int
    NumberOfTimes90DaysLate: int
    NumberRealEstateLoansOrLines: int
    NumberOfTime60_89DaysPastDueNotWorse: int = None
    NumberOfDependents: float = None


@app.get("/")
def root():
    """Endpoint racine, simple vérification que l'API tourne."""
    return {"status": "Credit Scoring API is running"}



@app.post("/score")
def score_client(client: ClientData):
    """
    Calcule le score de risque d'un client à partir de ses données brutes.
    """
    # Convertir les données reçues en DataFrame d'une seule ligne
    df = pd.DataFrame([client.model_dump()])

    # Renommer les colonnes vers les noms attendus par le pipeline
    # (les underscores dans les noms Pydantic remplacent les tirets originaux)
    df = df.rename(columns={
        "NumberOfTime30_59DaysPastDueNotWorse": "NumberOfTime30-59DaysPastDueNotWorse",
        "NumberOfTime60_89DaysPastDueNotWorse": "NumberOfTime60-89DaysPastDueNotWorse",
    })

    # Ajouter une colonne 'Unnamed: 0' factice, car rename_columns() l'attend
    df.insert(0, "Unnamed: 0", 0)

    # Appliquer le même pipeline que le batch
    df_clean = clean_pipeline(df)
    df_final = build_features(df_clean)

    # Prédire
    X = df_final.drop(columns=["customer_id"], errors="ignore")
    risk_score = float(model.predict_proba(X)[:, 1][0])

    return {"risk_score": round(risk_score, 4)}