"""
features.py

Feature engineering pour le scoring crédit.
Crée des variables dérivées à partir des colonnes brutes, en particulier
la combinaison des 3 colonnes de retard de paiement (30-59, 60-89, 90+ jours)
identifiées lors de l'EDA comme racontant une même histoire à des niveaux
de gravité différents.
"""

import pandas as pd


def add_total_late_payments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule le nombre total d'incidents de retard de paiement, tous niveaux
    de gravité confondus (30-59, 60-89, 90+ jours).

    Plutôt que de garder 3 colonnes séparées que le modèle doit apprendre à
    combiner lui-même, cette feature agrégée donne directement un signal
    de fréquence globale des incidents.

    Args:
        df: DataFrame contenant les colonnes times_30_59_days_late,
            times_60_89_days_late, times_90_days_late

    Returns:
        DataFrame avec une nouvelle colonne 'total_late_payments'
    """
    df = df.copy()
    df["total_late_payments"] = (
        df["times_30_59_days_late"]
        + df["times_60_89_days_late"]
        + df["times_90_days_late"]
    )
    return df


def add_max_delinquency_severity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Détermine le niveau de gravité maximal jamais atteint par le client.

    Valeurs possibles :
        0 = aucun retard
        1 = retard modéré (30-59 jours) au pire
        2 = retard sérieux (60-89 jours) au pire
        3 = retard grave (90+ jours) au pire

    Cette feature capture "le pire qui soit arrivé", complémentaire à
    total_late_payments qui capture "à quelle fréquence c'est arrivé".
    Un client avec 1 seul incident à 90+ jours est probablement plus
    risqué qu'un client avec 5 incidents à 30-59 jours seulement.

    Args:
        df: DataFrame contenant les colonnes times_30_59_days_late,
            times_60_89_days_late, times_90_days_late

    Returns:
        DataFrame avec une nouvelle colonne 'max_delinquency_severity'
    """
    df = df.copy()

    def _severity(row):
        if row["times_90_days_late"] > 0:
            return 3
        elif row["times_60_89_days_late"] > 0:
            return 2
        elif row["times_30_59_days_late"] > 0:
            return 1
        else:
            return 0

    df["max_delinquency_severity"] = df.apply(_severity, axis=1)
    return df


def add_credit_lines_per_dependent(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ratio du nombre de lignes de crédit ouvertes par personne à charge.

    Approxime la pression financière du foyer : un client avec beaucoup
    de lignes de crédit ouvertes ET beaucoup de personnes à charge gère
    une situation plus complexe qu'un client sans charge de famille.
    On ajoute +1 au dénominateur pour éviter une division par zéro
    quand number_of_dependents vaut 0.

    Args:
        df: DataFrame contenant open_credit_lines et number_of_dependents

    Returns:
        DataFrame avec une nouvelle colonne 'credit_lines_per_dependent'
    """
    df = df.copy()
    df["credit_lines_per_dependent"] = df["open_credit_lines"] / (
        df["number_of_dependents"] + 1
    )
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enchaîne toutes les étapes de feature engineering dans l'ordre.

    Args:
        df: DataFrame déjà nettoyé (sortie de preprocessing.clean_pipeline)

    Returns:
        DataFrame enrichi avec les nouvelles features
    """
    df = add_total_late_payments(df)
    df = add_max_delinquency_severity(df)
    df = add_credit_lines_per_dependent(df)
    return df