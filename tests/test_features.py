"""
test_features.py

Tests unitaires pour scoring_lib.preprocessing.
Chaque fonction de nettoyage est testée isolément, avec des cas simples
et explicites (petits DataFrames construits à la main), pour vérifier
le comportement exact attendu — pas juste "ça tourne sans erreur".
"""

import pandas as pd
import sys
import os

# Permet d'importer scoring_lib depuis le dossier racine du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scoring_lib.preprocessing import (
    clean_monthly_income,
    clean_number_of_dependents,
    filter_invalid_age,
    clean_pipeline,
)


def test_clean_monthly_income_flags_missing_values():
    """Une valeur manquante doit être flaguée à 1 et remplacée par -1."""
    df = pd.DataFrame({"MonthlyIncome": [5000, None, 3000]})
    result = clean_monthly_income(df)

    assert result["monthly_income_missing_flag"].tolist() == [0, 1, 0]
    assert result["monthly_income_raw"].tolist() == [5000, -1, 3000]


def test_clean_monthly_income_preserves_valid_values():
    """Les valeurs présentes ne doivent jamais être modifiées."""
    df = pd.DataFrame({"MonthlyIncome": [1000, 2500, 7800]})
    result = clean_monthly_income(df)

    assert result["monthly_income_raw"].tolist() == [1000, 2500, 7800]
    assert result["monthly_income_missing_flag"].tolist() == [0, 0, 0]


def test_clean_number_of_dependents_fills_with_zero():
    """Une valeur manquante de personnes à charge doit devenir 0."""
    df = pd.DataFrame({"NumberOfDependents": [2, None, 0]})
    result = clean_number_of_dependents(df)

    assert result["number_of_dependents"].tolist() == [2, 0, 0]


def test_filter_invalid_age_removes_zero_age():
    """Les lignes avec age <= 0 doivent être exclues."""
    df = pd.DataFrame({"age": [25, 0, 40, -5]})
    result = filter_invalid_age(df)

    assert result["age"].tolist() == [25, 40]
    assert len(result) == 2


def test_filter_invalid_age_keeps_all_valid_ages():
    """Si aucun âge n'est invalide, aucune ligne ne doit être supprimée."""
    df = pd.DataFrame({"age": [25, 30, 40]})
    result = filter_invalid_age(df)

    assert len(result) == 3


def test_clean_pipeline_runs_all_steps_together():
    """Le pipeline complet doit appliquer les 3 étapes dans le bon ordre."""
    df = pd.DataFrame({
        "age": [25, 0, 40],
        "MonthlyIncome": [5000, 3000, None],
        "NumberOfDependents": [1, 2, None],
    })
    result = clean_pipeline(df)

    # La ligne age=0 doit être exclue -> il reste 2 lignes
    assert len(result) == 2
    # Les colonnes attendues doivent toutes être présentes
    assert "monthly_income_missing_flag" in result.columns
    assert "number_of_dependents" in result.columns