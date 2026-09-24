"""
test_api.py

Tests d'intégration pour l'API de scoring crédit.
Utilise TestClient de FastAPI, qui simule des requêtes HTTP sans avoir
besoin qu'Uvicorn tourne réellement en arrière-plan.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root_endpoint_returns_status():
    """L'endpoint racine doit confirmer que l'API tourne."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Credit Scoring API is running"}


def test_score_endpoint_valid_client_returns_score():
    """Un client avec des données valides doit recevoir un score entre 0 et 1."""
    valid_client = {
        "age": 45,
        "RevolvingUtilizationOfUnsecuredLines": 0.5,
        "NumberOfTime30_59DaysPastDueNotWorse": 1,
        "DebtRatio": 0.3,
        "MonthlyIncome": 5000,
        "NumberOfOpenCreditLinesAndLoans": 6,
        "NumberOfTimes90DaysLate": 0,
        "NumberRealEstateLoansOrLines": 1,
        "NumberOfTime60_89DaysPastDueNotWorse": 0,
        "NumberOfDependents": 2,
    }
    response = client.post("/score", json=valid_client)

    assert response.status_code == 200
    result = response.json()
    assert "risk_score" in result
    assert 0.0 <= result["risk_score"] <= 1.0


def test_score_endpoint_rejects_invalid_age():
    """Un âge de 0 (ou négatif) doit être rejeté avec une erreur 422, pas planter."""
    invalid_client = {
        "age": 0,
        "RevolvingUtilizationOfUnsecuredLines": 0.5,
        "NumberOfTime30_59DaysPastDueNotWorse": 1,
        "DebtRatio": 0.3,
        "MonthlyIncome": 5000,
        "NumberOfOpenCreditLinesAndLoans": 6,
        "NumberOfTimes90DaysLate": 0,
        "NumberRealEstateLoansOrLines": 1,
        "NumberOfTime60_89DaysPastDueNotWorse": 0,
        "NumberOfDependents": 2,
    }
    response = client.post("/score", json=invalid_client)

    assert response.status_code == 422


def test_score_endpoint_rejects_negative_debt_ratio():
    """Un DebtRatio négatif doit être rejeté (ge=0 dans le schéma)."""
    invalid_client = {
        "age": 45,
        "RevolvingUtilizationOfUnsecuredLines": 0.5,
        "NumberOfTime30_59DaysPastDueNotWorse": 1,
        "DebtRatio": -0.5,
        "MonthlyIncome": 5000,
        "NumberOfOpenCreditLinesAndLoans": 6,
        "NumberOfTimes90DaysLate": 0,
        "NumberRealEstateLoansOrLines": 1,
        "NumberOfTime60_89DaysPastDueNotWorse": 0,
        "NumberOfDependents": 2,
    }
    response = client.post("/score", json=invalid_client)

    assert response.status_code == 422


def test_score_endpoint_missing_required_field():
    """Une requête sans un champ obligatoire (ex: age) doit être rejetée."""
    incomplete_client = {
        "RevolvingUtilizationOfUnsecuredLines": 0.5,
        "DebtRatio": 0.3,
        "NumberOfOpenCreditLinesAndLoans": 6,
        "NumberOfTimes90DaysLate": 0,
        "NumberRealEstateLoansOrLines": 1,
    }
    response = client.post("/score", json=incomplete_client)

    assert response.status_code == 422