-- Nettoyage des données brutes de scoring crédit — version PostgreSQL (legacy)
-- Gère les valeurs manquantes explicitement plutôt que de les supprimer,
-- car l'absence de revenu déclaré est en soi une information prédictive.

CREATE TABLE cleaned_credit_data AS
SELECT
    id AS customer_id,
    serious_dlqin2yrs AS target,
    revolving_utilization,
    age,
    times_30_59_days_late,
    debt_ratio,
    COALESCE(monthly_income, -1) AS monthly_income_raw,
    CASE WHEN monthly_income IS NULL THEN 1 ELSE 0 END AS monthly_income_missing_flag,
    open_credit_lines,
    times_90_days_late,
    real_estate_loans,
    times_60_89_days_late,
    COALESCE(number_of_dependents, 0) AS number_of_dependents
FROM raw_credit_data
WHERE age > 0;