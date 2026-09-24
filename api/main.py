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
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
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
    Chaque champ a des bornes réalistes pour rejeter les données aberrantes
    avant même d'atteindre le pipeline de scoring.
    """
    age: int = Field(..., gt=0, le=120, description="Âge du client, doit être positif")
    RevolvingUtilizationOfUnsecuredLines: float = Field(..., ge=0)
    NumberOfTime30_59DaysPastDueNotWorse: int = Field(0, ge=0)
    DebtRatio: float = Field(..., ge=0)
    MonthlyIncome: float = Field(None, ge=0)
    NumberOfOpenCreditLinesAndLoans: int = Field(..., ge=0)
    NumberOfTimes90DaysLate: int = Field(..., ge=0)
    NumberRealEstateLoansOrLines: int = Field(..., ge=0)
    NumberOfTime60_89DaysPastDueNotWorse: int = Field(0, ge=0)
    NumberOfDependents: float = Field(None, ge=0)


@app.get("/")
def root():
    """Endpoint racine, simple vérification que l'API tourne."""
    return {"status": "Credit Scoring API is running"}



@app.post("/score")
def score_client(client: ClientData):
    """
    Calcule le score de risque d'un client à partir de ses données brutes.
    """
    try:
        df = pd.DataFrame([client.model_dump()])

        df = df.rename(columns={
            "NumberOfTime30_59DaysPastDueNotWorse": "NumberOfTime30-59DaysPastDueNotWorse",
            "NumberOfTime60_89DaysPastDueNotWorse": "NumberOfTime60-89DaysPastDueNotWorse",
        })

        df.insert(0, "Unnamed: 0", 0)

        df_clean = clean_pipeline(df)
        df_final = build_features(df_clean)

        X = df_final.drop(columns=["customer_id"], errors="ignore")
        risk_score = float(model.predict_proba(X)[:, 1][0])

        return {"risk_score": round(risk_score, 4)}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du calcul du score : {str(e)}"
        )