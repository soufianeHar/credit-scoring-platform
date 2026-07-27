"""
preprocessing.py

Fonctions de nettoyage et préparation des données de scoring crédit.
Reproduit en Python la logique déjà validée en SQL (voir sql/01_cleaning_legacy.sql),
pour permettre le traitement de données arrivant hors data warehouse
(ex: une seule ligne envoyée à l'API de scoring en temps réel, Semaine 6).
"""

import pandas as pd


def clean_monthly_income(df: pd.DataFrame) -> pd.DataFrame:
    """
    Gère les valeurs manquantes de la colonne MonthlyIncome.

    Plutôt que d'imputer une valeur arbitraire (moyenne, médiane), on garde une
    valeur sentinelle (-1) ET un flag binaire séparé. En scoring crédit, l'absence
    de revenu déclaré est en soi une information prédictive (souvent corrélée à un
    profil plus risqué) — la cacher par une imputation classique perdrait ce signal.

    Args:
        df: DataFrame contenant une colonne 'MonthlyIncome'

    Returns:
        DataFrame avec deux nouvelles colonnes :
        - monthly_income_raw : valeur originale, ou -1 si manquante
        - monthly_income_missing_flag : 1 si la valeur était manquante, 0 sinon
    """
    df = df.copy()
    df["monthly_income_missing_flag"] = df["MonthlyIncome"].isna().astype(int)
    df["monthly_income_raw"] = df["MonthlyIncome"].fillna(-1)
    return df


def clean_number_of_dependents(df: pd.DataFrame) -> pd.DataFrame:
    """
    Gère les valeurs manquantes de la colonne NumberOfDependents.

    Ici, contrairement au revenu, une valeur manquante est traitée comme 0
    personne à charge — hypothèse raisonnable par défaut (pas d'indication
    contraire), et le volume de valeurs manquantes est marginal (~2.6%)
    par rapport à MonthlyIncome (~20%).

    Args:
        df: DataFrame contenant une colonne 'NumberOfDependents'

    Returns:
        DataFrame avec la colonne 'number_of_dependents' nettoyée
    """
    df = df.copy()
    df["number_of_dependents"] = df["NumberOfDependents"].fillna(0)
    return df


def filter_invalid_age(df: pd.DataFrame) -> pd.DataFrame:
    """
    Exclut les lignes avec un âge invalide (age <= 0).

    Reproduit le filtre WHERE age > 0 de la requête SQL de nettoyage.
    Sur le dataset Give Me Some Credit, ce filtre exclut exactement
    1 ligne sur 150 000 (client avec age = 0, probable erreur de saisie).

    Args:
        df: DataFrame contenant une colonne 'age'

    Returns:
        DataFrame filtré, sans les lignes à âge invalide
    """
    return df[df["age"] > 0].copy()


def clean_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enchaîne toutes les étapes de nettoyage dans l'ordre correct.

    C'est le point d'entrée unique à utiliser par le pipeline d'orchestration
    (Semaine 5) et l'API de scoring (Semaine 6), pour garantir que les deux
    appliquent exactement la même logique de nettoyage.

    Args:
        df: DataFrame brut (colonnes originales du dataset Give Me Some Credit)

    Returns:
        DataFrame nettoyé, prêt pour le feature engineering
    """
    df = filter_invalid_age(df)
    df = clean_monthly_income(df)
    df = clean_number_of_dependents(df)
    return df