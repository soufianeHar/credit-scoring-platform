# SQL Transformations — Legacy (PostgreSQL) vs BigQuery

## Contexte
Ce dossier contient deux versions équivalentes de la même transformation de nettoyage,
écrites respectivement en PostgreSQL (simulant une syntaxe SQL "legacy" type Teradata)
et en BigQuery SQL — dans une logique de migration cloud.

## Fichiers
- `01_cleaning_legacy.sql` — version PostgreSQL
- `02_cleaning_bigquery.sql` — version BigQuery

## Résultat
Les deux requêtes produisent un résultat identique : 149 999 lignes
(150 000 lignes brutes, 1 ligne exclue pour âge invalide = 0).

## Différences de syntaxe observées

| Aspect | PostgreSQL | BigQuery |
|---|---|---|
| Référence de table | `nom_table` | Chemin complet `projet.dataset.table` obligatoire |
| Conversion de type sécurisée | Typage strict à l'import (erreur si incompatible) | `SAFE_CAST(x AS FLOAT64)` — retourne NULL au lieu de planter |
| Noms de colonnes avec caractères spéciaux | Guillemets doubles `"..."` si besoin | Backticks `` `...` `` obligatoires (ex: colonnes avec tirets) |
| Gestion des valeurs manquantes à l'import | Nécessite une valeur NULL explicite définie à l'import (ex: "NA") | Plus permissif — bascule automatiquement la colonne en STRING si types mixtes |

## Enseignement clé
BigQuery est plus tolérant à l'ingestion (accepte des données mal typées sans échouer),
mais reporte la responsabilité de la conversion sur les requêtes de transformation
via `SAFE_CAST`. PostgreSQL est plus strict à l'import, ce qui force une détection
des problèmes de données plus tôt dans le pipeline.