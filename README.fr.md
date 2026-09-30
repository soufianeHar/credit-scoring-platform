# Plateforme de Scoring Crédit — Pipeline MLOps de bout en bout

*[English version](README.md)*

Projet portfolio inspiré d'une fiche de poste Data Scientist (BTechnologie),
construit pour démontrer les compétences d'industrialisation ML au-delà de
la simple modélisation : SQL de production, orchestration, API temps réel,
monitoring de drift, et un agent conversationnel sur les données.

## Ce que fait le projet

À partir du dataset [Give Me Some Credit](https://www.kaggle.com/c/GiveMeSomeCredit)
(150 000 clients, scoring de risque de défaut) :

1. **Nettoyage et migration SQL** — PostgreSQL puis BigQuery, avec les
   différences de syntaxe documentées
2. **Librairie Python testée** (`scoring_lib`) — nettoyage et feature
   engineering réutilisés par le pipeline batch ET l'API temps réel
3. **Modélisation** — comparaison de 4 modèles (validation croisée),
   LightGBM retenu, interprété avec SHAP
4. **Orchestration** (Prefect) — pipeline automatisé qui écrit les scores
   dans BigQuery, avec réessais automatiques
5. **API de scoring temps réel** (FastAPI) — un client, une requête, un
   score, avec validation stricte des entrées
6. **Monitoring** (Evidently + Streamlit) — détection de drift entre les
   données d'entraînement et un scénario de production simulé
7. **Agent Talk-to-Data** (Ollama, local et gratuit) — questions en
   français sur les clients scorés, SQL généré puis validé avant exécution

## Architecture

Voir [`docs/architecture.md`](docs/architecture.md) pour le diagramme complet.

## Démarrage rapide

```powershell
git clone https://github.com/soufianeHar/credit-scoring-platform.git
cd credit-scoring-platform
poetry install
```

| Brique | Commande | Doc |
|---|---|---|
| Tests | `pytest tests\ -v` | — |
| Pipeline de scoring | `py -c "from pipeline.scoring_flow import scoring_pipeline; scoring_pipeline()"` | [`pipeline/`](pipeline/) |
| API temps réel | `uvicorn api.main:app --reload` puis `/docs` | [`api/README.md`](api/README.md) |
| Dashboard monitoring | `streamlit run monitoring/dashboard.py` | [`monitoring/README.md`](monitoring/README.md) |
| Agent Talk-to-Data | `streamlit run agent/chat_ui.py` | [`agent/README.md`](agent/README.md) |

## Stack technique

Python, PostgreSQL, Google BigQuery, Poetry, pytest, scikit-learn, XGBoost,
LightGBM, SHAP, Prefect, FastAPI, Evidently AI, Streamlit, Ollama, sqlglot.

## Choix documentés et limites connues

- Le modèle utilise `scale_pos_weight` pour le déséquilibre de classes
  (6.7% de défauts) : les scores discriminent bien mais ne sont pas des
  probabilités calibrées.
- La table BigQuery `client_scores` est recréée à chaque exécution du
  pipeline (Sandbox gratuit, expiration à 60 jours).
- Le monitoring de drift utilise des données de production simulées,
  faute d'un vrai flux (hors périmètre d'un projet portfolio).
- La sécurité de l'agent SQL est au niveau du code (validation avant
  exécution), pas encore au niveau des droits BigQuery eux-mêmes — voir
  [`agent/README.md`](agent/README.md).

## Auteur

Soufiane Harzane — [GitHub](https://github.com/soufianeHar)