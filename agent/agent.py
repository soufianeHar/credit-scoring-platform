"""
agent.py

Agent Talk-to-Data : question en français -> SQL BigQuery -> résultat.
Le LLM (local, via Ollama) ne voit jamais les données, seulement le schéma.
Son SQL passe par validate_sql avant toute exécution (voir query_tools.py).
"""

import os
import re
import ollama

from agent.query_tools import SCHEMA_DESCRIPTION, TABLE_ID, run_query

DEFAULT_MODEL = os.getenv("AGENT_MODEL", "qwen2.5-coder:3b")
MAX_ATTEMPTS = 3

SYSTEM_PROMPT = f"""Tu traduis des questions en français en requêtes SQL BigQuery.

Règles :
- Réponds avec UNE SEULE requête SQL dans un bloc ```sql, sans aucune explication.
- Uniquement des SELECT, uniquement sur la table `{TABLE_ID}` (nom complet entre backticks).
- Dialecte BigQuery (COUNTIF, SAFE_DIVIDE, ROUND...).
- Si la question ne peut pas être traitée avec cette table, réponds exactement : IMPOSSIBLE

{SCHEMA_DESCRIPTION}

Exemples :

Question : Combien de clients ont plus de 60 ans ?
```sql
SELECT COUNT(*) AS nb_clients FROM `{TABLE_ID}` WHERE age > 60
```

Question : Quel est le score moyen par tranche d'âge ?
```sql
SELECT CASE WHEN age < 30 THEN 'moins de 30' WHEN age < 50 THEN '30-49' ELSE '50 et plus' END AS tranche_age,
       ROUND(AVG(risk_score), 3) AS score_moyen
FROM `{TABLE_ID}` GROUP BY tranche_age ORDER BY tranche_age
```

Question : Quel est le taux de défaut réel des clients dont le score dépasse 0.8 ?
```sql
SELECT ROUND(AVG(target) * 100, 2) AS taux_defaut_pct FROM `{TABLE_ID}` WHERE risk_score > 0.8
```

Question : Quels sont les 5 clients les plus risqués ?
```sql
SELECT customer_id, age, risk_score FROM `{TABLE_ID}` ORDER BY risk_score DESC LIMIT 5
```
"""


def extract_sql(text: str) -> str | None:
    """Extrait la requête SQL de la réponse du modèle (None si IMPOSSIBLE)."""
    if text.strip().upper().startswith("IMPOSSIBLE"):
        return None
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    sql = match.group(1) if match else text
    return sql.strip().rstrip(";").strip()


def ask(question: str, model: str = DEFAULT_MODEL) -> dict:
    """
    Répond à une question. Si le SQL est refusé ou échoue sur BigQuery,
    l'erreur est renvoyée au modèle qui corrige (MAX_ATTEMPTS essais).
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    sql, last_error = None, None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = ollama.chat(model=model, messages=messages, options={"temperature": 0})
        content = response["message"]["content"]
        sql = extract_sql(content)

        if sql is None:
            return {"question": question, "model": model, "sql": None, "data": None,
                    "attempts": attempt, "error": "Question non traitable avec cette table."}
        try:
            data = run_query(sql)
            return {"question": question, "model": model, "sql": sql, "data": data,
                    "attempts": attempt, "error": None}
        except Exception as e:
            last_error = str(e)[:500]
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content":
                f"Cette requête a échoué : {last_error}\nCorrige-la. Réponds uniquement avec un bloc ```sql."})

    return {"question": question, "model": model, "sql": sql, "data": None,
            "attempts": MAX_ATTEMPTS, "error": last_error}


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "Quel est le score moyen des clients de moins de 30 ans ?"
    result = ask(q)
    print(f"Modèle : {result['model']} | essais : {result['attempts']}")
    print(f"SQL : {result['sql']}")
    print(result["data"] if result["error"] is None else f"Erreur : {result['error']}")