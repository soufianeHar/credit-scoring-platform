"""Tests de la validation SQL de l'agent : ce qui doit passer, et surtout ce qui doit être refusé."""

import pytest
from agent.query_tools import validate_sql, UnsafeSQLError

TABLE = "`credit-scoring-platform.credit_scoring.client_scores`"


def test_accepts_simple_select():
    assert validate_sql(f"SELECT COUNT(*) FROM {TABLE}")


def test_accepts_cte():
    sql = f"WITH jeunes AS (SELECT * FROM {TABLE} WHERE age < 30) SELECT AVG(risk_score) FROM jeunes"
    assert validate_sql(sql)


@pytest.mark.parametrize("sql", [
    f"DELETE FROM {TABLE} WHERE age > 0",
    f"DROP TABLE {TABLE}",
    f"UPDATE {TABLE} SET risk_score = 0 WHERE age > 0",
    f"INSERT INTO {TABLE} (customer_id) VALUES (1)",
])
def test_rejects_write_statements(sql):
    with pytest.raises(UnsafeSQLError):
        validate_sql(sql)


def test_rejects_multiple_statements():
    with pytest.raises(UnsafeSQLError):
        validate_sql(f"SELECT 1 FROM {TABLE}; DROP TABLE {TABLE}")


def test_rejects_other_table():
    with pytest.raises(UnsafeSQLError):
        validate_sql("SELECT * FROM `credit-scoring-platform.credit_scoring.autre_table`")