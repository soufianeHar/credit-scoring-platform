"""
test_build_features.py

Tests unitaires pour scoring_lib.features.
Même logique que test_features.py : mini-DataFrames construits à la main,
valeurs choisies pour connaître le résultat attendu à l'avance.
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scoring_lib.features import (
    add_total_late_payments,
    add_max_delinquency_severity,
    add_credit_lines_per_dependent,
    build_features,
)


def test_add_total_late_payments_sums_all_three_columns():
    """Le total doit être la somme exacte des 3 colonnes de retard."""
    df = pd.DataFrame({
        "times_30_59_days_late": [1, 0, 2],
        "times_60_89_days_late": [0, 1, 1],
        "times_90_days_late": [2, 0, 0],
    })
    result = add_total_late_payments(df)

    assert result["total_late_payments"].tolist() == [3, 1, 3]


def test_add_max_delinquency_severity_picks_worst_case():
    """La gravité doit refléter le pire incident, pas la fréquence."""
    df = pd.DataFrame({
        "times_30_59_days_late": [1, 0, 5, 0],
        "times_60_89_days_late": [0, 1, 0, 0],
        "times_90_days_late": [0, 0, 0, 0],
    })
    result = add_max_delinquency_severity(df)

    # ligne 0: seulement 30-59 -> sévérité 1
    # ligne 1: seulement 60-89 -> sévérité 2
    # ligne 2: 5 incidents 30-59 mais rien de pire -> sévérité 1 (pas 5)
    # ligne 3: aucun incident -> sévérité 0
    assert result["max_delinquency_severity"].tolist() == [1, 2, 1, 0]


def test_add_max_delinquency_severity_prioritizes_90_days():
    """Un seul incident à 90+ jours doit dominer, même avec d'autres retards."""
    df = pd.DataFrame({
        "times_30_59_days_late": [3],
        "times_60_89_days_late": [2],
        "times_90_days_late": [1],
    })
    result = add_max_delinquency_severity(df)

    assert result["max_delinquency_severity"].tolist() == [3]


def test_add_credit_lines_per_dependent_handles_zero_dependents():
    """Avec 0 personne à charge, le ratio doit diviser par 1 (pas par 0)."""
    df = pd.DataFrame({
        "open_credit_lines": [4],
        "number_of_dependents": [0],
    })
    result = add_credit_lines_per_dependent(df)

    assert result["credit_lines_per_dependent"].tolist() == [4.0]


def test_add_credit_lines_per_dependent_divides_correctly():
    """Avec des personnes à charge, le ratio doit être correctement calculé."""
    df = pd.DataFrame({
        "open_credit_lines": [6],
        "number_of_dependents": [2],
    })
    result = add_credit_lines_per_dependent(df)

    # 6 / (2 + 1) = 2.0
    assert result["credit_lines_per_dependent"].tolist() == [2.0]


def test_build_features_adds_all_expected_columns():
    """Le pipeline complet doit produire toutes les colonnes attendues."""
    df = pd.DataFrame({
        "times_30_59_days_late": [1],
        "times_60_89_days_late": [0],
        "times_90_days_late": [0],
        "open_credit_lines": [3],
        "number_of_dependents": [1],
    })
    result = build_features(df)

    assert "total_late_payments" in result.columns
    assert "max_delinquency_severity" in result.columns
    assert "credit_lines_per_dependent" in result.columns