"""
evaluate.py

Compare deux modèles Ollama sur un jeu de questions fixe.
Pour chaque question, on connaît le SQL attendu (ou juste la vérification
que la requête s'exécute), ce qui permet un taux de réussite chiffré,
plutôt qu'une impression après une ou deux questions.
"""

import time
from agent.agent import ask

QUESTIONS = [
    "Combien de clients y a-t-il au total ?",
    "Quel est le score moyen des clients de moins de 30 ans ?",
    "Quel est le taux de défaut réel des clients dont le score dépasse 0.8 ?",
    "Quel est le revenu mensuel moyen des clients qui ont déclaré un revenu ?",
    "Quels sont les 5 clients avec le score de risque le plus élevé ?",
    "Combien de clients ont eu au moins un retard de paiement de 90 jours ou plus ?",
    "Quel est le score moyen par tranche d'âge (moins de 30, 30-49, 50 et plus) ?",
    "Quel est l'âge moyen des clients qui ont un score supérieur à 0.5 ?",
    "Combien de clients n'ont déclaré aucun revenu ?",
    "Quel est le ratio d'endettement moyen des clients de moins de 40 ans ?",
]


def evaluate(model: str) -> list[dict]:
    """Pose toutes les questions à un modèle et mesure le résultat de chacune."""
    results = []
    for question in QUESTIONS:
        start = time.time()
        result = ask(question, model=model)
        duration = round(time.time() - start, 1)

        success = result["error"] is None and result["sql"] is not None
        results.append({
            "question": question,
            "success": success,
            "attempts": result["attempts"],
            "duration_s": duration,
            "sql": result["sql"],
            "error": result["error"],
        })
    return results


def print_report(model: str, results: list[dict]) -> None:
    """Affiche un résumé lisible : taux de réussite, puis le détail par question."""
    n_success = sum(r["success"] for r in results)
    total_time = sum(r["duration_s"] for r in results)

    print(f"\n=== {model} ===")
    print(f"Réussite : {n_success}/{len(results)} | Temps total : {total_time:.0f}s")
    for r in results:
        marker = "OK" if r["success"] else "ECHEC"
        print(f"  [{marker}] ({r['attempts']} essai(s), {r['duration_s']}s) {r['question']}")
        if not r["success"]:
            print(f"         -> {r['error']}")


if __name__ == "__main__":
    for model in ["qwen2.5-coder:3b", "qwen2.5-coder:7b"]:
        results = evaluate(model)
        print_report(model, results)