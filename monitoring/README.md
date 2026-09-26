# Monitoring & Détection de Drift

## Objectif
Surveiller si les données reçues en production (nouveaux clients) s'éloignent
statistiquement des données sur lesquelles le modèle a été entraîné — signal
qu'un ré-entraînement pourrait être nécessaire.

## Approche
- **Data reference** : dataset d'entraînement original (Semaine 4)
- **Data actuelle** : simulée pour la démo (voir `data/05_monitoring.ipynb`),
  représentant un scénario économique dégradé (baisse de revenus,
  hausse de l'endettement, population plus jeune)
- **Outil** : Evidently AI, test de distance de Wasserstein normalisée
  par variable, seuil de drift global à 50% des colonnes

## Résultat observé
Sur 14 variables surveillées, 2 ont montré un drift statistiquement
significatif (`age`, `debt_ratio`), soit 14.3% — sous le seuil de drift
global (50%). `monthly_income_raw`, bien que modifiée dans la simulation,
n'a pas été détectée comme ayant drifté : sa forte variance naturelle
absorbe une baisse de 10-30%, illustrant que la détection de drift dépend
de l'ampleur du changement **relatif à la variabilité naturelle** de
chaque variable, pas seulement du changement en valeur absolue.

## Lancer le dashboard

```powershell
streamlit run monitoring/dashboard.py
```

## Limite connue de cette démo
Les "données actuelles" sont simulées, pas de vraies données de production
(hors périmètre d'un projet portfolio). En production réelle, ce dashboard
se connecterait à un flux de données réel (nouveaux clients scorés chaque
jour) plutôt qu'à une simulation.