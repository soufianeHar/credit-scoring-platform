from agent.agent import extract_sql


def test_extracts_sql_from_fenced_block():
    text = "Voici :\n```sql\nSELECT 1 FROM t;\n```\nCette requête fait..."
    assert extract_sql(text) == "SELECT 1 FROM t"


def test_extracts_sql_surrounded_by_explanations():
    text = "Bien sûr !\n\n```sql\nSELECT AVG(x) FROM t WHERE a < 3\n```\n\n1. Elle filtre..."
    assert extract_sql(text) == "SELECT AVG(x) FROM t WHERE a < 3"


def test_returns_none_when_impossible():
    assert extract_sql("IMPOSSIBLE") is None


def test_accepts_bare_select_without_fence():
    assert extract_sql("SELECT 1 FROM t") == "SELECT 1 FROM t"