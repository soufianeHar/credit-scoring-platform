# API de Scoring Crédit — Temps Réel

## Objectif
Cette API calcule le score de risque de défaut d'un client en temps réel,
à partir de ses données brutes. Elle réutilise la même logique de
nettoyage/feature engineering que le pipeline batch (voir `pipeline/`),
garantissant une cohérence parfaite entre scoring en masse et scoring
à la demande.

## Lancer l'API

```powershell
uvicorn api.main:app --reload
```

L'API démarre sur `http://127.0.0.1:8000`.

## Endpoints

### `GET /`
Vérification que l'API tourne.

**Réponse :**
```json
{"status": "Credit Scoring API is running"}
```

### `POST /score`
Calcule le score de risque d'un client.

**Requête (exemple) :**
```json
{
  "age": 45,
  "RevolvingUtilizationOfUnsecuredLines": 0.5,
  "NumberOfTime30_59DaysPastDueNotWorse": 1,
  "DebtRatio": 0.3,
  "MonthlyIncome": 5000,
  "NumberOfOpenCreditLinesAndLoans": 6,
  "NumberOfTimes90DaysLate": 0,
  "NumberRealEstateLoansOrLines": 1,
  "NumberOfTime60_89DaysPastDueNotWorse": 0,
  "NumberOfDependents": 2
}
```

**Réponse :**
```json
{"risk_score": 0.7506}
```

`risk_score` est une probabilité entre 0 et 1 (plus élevé = plus risqué).
Note : le modèle utilise `scale_pos_weight` pour gérer le déséquilibre de
classes (6.7% de défauts) — les scores sont donc bien discriminants mais
pas parfaitement calibrés en probabilité réelle.

## Validation des données

Chaque champ est validé avant traitement (via Pydantic) :
- `age` : entre 1 et 120
- Tous les champs numériques : doivent être positifs ou nuls
- Une requête invalide retourne une erreur `422` avec le détail du problème,
  pas un crash serveur.

## Documentation interactive

Une fois l'API lancée, une interface de test est disponible sur :
`http://127.0.0.1:8000/docs`

## Tests

```powershell
pytest tests\test_api.py -v
```