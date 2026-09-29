"""
query_tools.py

Couche d'accès sécurisée à BigQuery pour l'agent Talk-to-Data.
Le SQL généré par un LLM n'est jamais exécuté tel quel : il est d'abord
validé (SELECT seul, une seule instruction, table autorisée), puis exécuté
avec un plafond de volume scanné et un nombre de lignes limité.
"""

import pandas as pd
import sqlglot
from sqlglot import exp
from google.cloud import bigquery

BQ_PROJECT = "credit-scoring-platform"
ALLOWED_DATASET = "credit_scoring"
ALLOWED_TABLE = "client_scores"
TABLE_ID = f"{BQ_PROJECT}.{ALLOWED_DATASET}.{ALLOWED_TABLE}"

MAX_BYTES_BILLED = 100 * 1024 * 1024  # 100 Mo, la table en pèse 21
MAX_ROWS = 100

# Ce texte sera fourni au LLM (Tâche 40) pour qu'il connaisse la table.
SCHEMA_DESCRIPTION = f"""
Table BigQuery : `{TABLE_ID}` (149 999 clients, un score par client).

Colonnes :
- customer_id : identifiant du client
- target : défaut réellement constaté (1 = défaut grave sous 2 ans, 0 = non)
- revolving_utilization : taux d'utilisation des lignes de crédit (0 à 1 et plus)
- age : âge en années
- times_30_59_days_late, times_60_89_days_late, times_90_days_late :
  nombre de retards de paiement, par niveau de gravité
- debt_ratio : ratio d'endettement (quelques valeurs extrêmes possibles)
- open_credit_lines : nombre de lignes de crédit ouvertes
- real_estate_loans : nombre de prêts immobiliers
- monthly_income_raw : revenu mensuel (-1 si non déclaré)
- monthly_income_missing_flag : 1 si le revenu n'est pas déclaré, 0 sinon
- number_of_dependents : nombre de personnes à charge
- total_late_payments : somme des trois colonnes de retards
- max_delinquency_severity : 0 aucun retard, 1 = 30-59j, 2 = 60-89j, 3 = 90j et plus
- credit_lines_per_dependent : lignes de crédit par personne à charge
- risk_score : score du modèle (0 à 1, plus haut = plus risqué,
  pas une probabilité calibrée)
- scored_at : date et heure du scoring
"""


class UnsafeSQLError(ValueError):
    """Levée quand une requête SQL n'est pas autorisée."""


def validate_sql(sql: str) -> str:
    """
    Vérifie qu'une requête est un SELECT unique portant uniquement sur la
    table autorisée. Retourne la requête si elle est valide, sinon lève
    UnsafeSQLError.
    """
    try:
        statements = [s for s in sqlglot.parse(sql, read="bigquery") if s is not None]
    except sqlglot.errors.SqlglotError as e:
        raise UnsafeSQLError(f"SQL invalide : {e}")

    if len(statements) != 1:
        raise UnsafeSQLError("Une seule requête est autorisée.")

    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.Union)):
        raise UnsafeSQLError("Seules les requêtes SELECT sont autorisées.")

    # Les noms définis par un WITH (CTE) ne sont pas de vraies tables
    cte_names = {cte.alias_or_name for cte in tree.find_all(exp.CTE)}

    for table in tree.find_all(exp.Table):
        if table.name in cte_names and not table.db:
            continue
        if table.name != ALLOWED_TABLE or (table.db and table.db != ALLOWED_DATASET):
            raise UnsafeSQLError(f"Table non autorisée : {table.name}")

    return sql


def run_query(sql: str, max_rows: int = MAX_ROWS) -> pd.DataFrame:
    """Valide puis exécute une requête, avec plafond de volume et de lignes."""
    safe_sql = validate_sql(sql)

    client = bigquery.Client(project=BQ_PROJECT)
    job_config = bigquery.QueryJobConfig(
        default_dataset=f"{BQ_PROJECT}.{ALLOWED_DATASET}",
        maximum_bytes_billed=MAX_BYTES_BILLED,
    )
    job = client.query(safe_sql, job_config=job_config)
    return job.result(max_results=max_rows).to_dataframe()


if __name__ == "__main__":
    demo = (
        "SELECT COUNT(*) AS nb_clients, ROUND(AVG(risk_score), 3) AS score_moyen "
        f"FROM `{TABLE_ID}`"
    )
    print(run_query(demo))