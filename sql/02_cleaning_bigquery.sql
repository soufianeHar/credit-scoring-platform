-- Nettoyage des données brutes de scoring crédit — version BigQuery (migration)
-- Équivalent fonctionnel de 01_cleaning_legacy.sql, adapté à la syntaxe BigQuery.
-- Différences clés : chemin de table complet, SAFE_CAST pour conversions sécurisées,
-- backticks pour les colonnes contenant des tirets.

CREATE TABLE `credit-scoring-platform.credit_scoring.cleaned_credit_data_bq` AS
SELECT
    int64_field_0 AS customer_id,
    SeriousDlqin2yrs AS target,
    RevolvingUtilizationOfUnsecuredLines AS revolving_utilization,
    age,
    `NumberOfTime30-59DaysPastDueNotWorse` AS times_30_59_days_late,
    DebtRatio AS debt_ratio,
    COALESCE(SAFE_CAST(MonthlyIncome AS FLOAT64), -1) AS monthly_income_raw,
    CASE WHEN SAFE_CAST(MonthlyIncome AS FLOAT64) IS NULL THEN 1 ELSE 0 END AS monthly_income_missing_flag,
    NumberOfOpenCreditLinesAndLoans AS open_credit_lines,
    NumberOfTimes90DaysLate AS times_90_days_late,
    NumberRealEstateLoansOrLines AS real_estate_loans,
    `NumberOfTime60-89DaysPastDueNotWorse` AS times_60_89_days_late,
    COALESCE(SAFE_CAST(NumberOfDependents AS FLOAT64), 0) AS number_of_dependents
FROM `credit-scoring-platform.credit_scoring.raw_credit_data`
WHERE age > 0;