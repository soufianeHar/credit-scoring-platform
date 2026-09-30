# Credit Scoring Platform — End-to-End MLOps Pipeline

*[Version française](README.fr.md)*

Portfolio project inspired by a Data Scientist job posting (BTechnologie),
built to demonstrate ML industrialization skills beyond modeling alone:
production SQL, orchestration, a real-time API, drift monitoring, and a
conversational agent over the data.

## What it does

Using the [Give Me Some Credit](https://www.kaggle.com/c/GiveMeSomeCredit)
dataset (150,000 clients, credit default risk scoring):

1. **SQL cleaning and migration** — PostgreSQL then BigQuery, with the
   syntax differences documented
2. **Tested Python library** (`scoring_lib`) — cleaning and feature
   engineering reused by both the batch pipeline AND the real-time API
3. **Modeling** — 4 models compared (cross-validation), LightGBM selected,
   interpreted with SHAP
4. **Orchestration** (Prefect) — automated pipeline that writes scores to
   BigQuery, with automatic retries
5. **Real-time scoring API** (FastAPI) — one client, one request, one
   score, with strict input validation
6. **Monitoring** (Evidently + Streamlit) — drift detection between
   training data and a simulated production scenario
7. **Talk-to-Data agent** (Ollama, local and free) — questions in French
   about scored clients, SQL generated then validated before execution

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full diagram.

## Quick start

```powershell
git clone https://github.com/soufianeHar/credit-scoring-platform.git
cd credit-scoring-platform
poetry install
```

| Component | Command | Docs |
|---|---|---|
| Tests | `pytest tests\ -v` | — |
| Scoring pipeline | `py -c "from pipeline.scoring_flow import scoring_pipeline; scoring_pipeline()"` | [`pipeline/`](pipeline/) |
| Real-time API | `uvicorn api.main:app --reload` then `/docs` | [`api/README.md`](api/README.md) |
| Monitoring dashboard | `streamlit run monitoring/dashboard.py` | [`monitoring/README.md`](monitoring/README.md) |
| Talk-to-Data agent | `streamlit run agent/chat_ui.py` | [`agent/README.md`](agent/README.md) |

## Tech stack

Python, PostgreSQL, Google BigQuery, Poetry, pytest, scikit-learn, XGBoost,
LightGBM, SHAP, Prefect, FastAPI, Evidently AI, Streamlit, Ollama, sqlglot.

## Documented choices and known limitations

- The model uses `scale_pos_weight` for class imbalance (6.7% defaults):
  scores discriminate well but are not calibrated probabilities.
- The BigQuery table `client_scores` is recreated on each pipeline run
  (free Sandbox tier, 60-day expiration).
- Drift monitoring uses simulated production data, since a real data
  stream is out of scope for a portfolio project.
- The agent's SQL safety layer is enforced in code (validation before
  execution), not yet at the BigQuery permission level — see
  [`agent/README.md`](agent/README.md).

## Author

Soufiane Harzane — [GitHub](https://github.com/soufianeHar)