# Databricks notebook source
# MAGIC %pip install lightgbm

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

from pyspark.sql import functions as F

spark.sql("CREATE VOLUME IF NOT EXISTS workspace.default.credit_data")

df = (spark.read
      .option("header", True)
      .option("inferSchema", True)
      .option("nullValue", "NA")
      .csv("/Volumes/workspace/default/credit_data/cs-training.csv"))

df = df.withColumnRenamed(df.columns[0], "customer_id")
print("Lignes lues :", df.count())

# COMMAND ----------

COLUMN_MAPPING = {
    "SeriousDlqin2yrs": "target",
    "RevolvingUtilizationOfUnsecuredLines": "revolving_utilization",
    "NumberOfTime30-59DaysPastDueNotWorse": "times_30_59_days_late",
    "DebtRatio": "debt_ratio",
    "NumberOfOpenCreditLinesAndLoans": "open_credit_lines",
    "NumberOfTimes90DaysLate": "times_90_days_late",
    "NumberRealEstateLoansOrLines": "real_estate_loans",
    "NumberOfTime60-89DaysPastDueNotWorse": "times_60_89_days_late",
}


def rename_columns(df):
    for old, new in COLUMN_MAPPING.items():
        df = df.withColumnRenamed(old, new)
    return df


def filter_invalid_age(df):
    return df.filter(F.col("age") > 0)


def clean_monthly_income(df):
    return (df
        .withColumn("monthly_income_missing_flag", F.col("MonthlyIncome").isNull().cast("int"))
        .withColumn("monthly_income_raw", F.coalesce(F.col("MonthlyIncome"), F.lit(-1)).cast("double"))
        .drop("MonthlyIncome"))


def clean_number_of_dependents(df):
    return (df
        .withColumn("number_of_dependents", F.coalesce(F.col("NumberOfDependents"), F.lit(0)).cast("double"))
        .drop("NumberOfDependents"))


def clean_pipeline(df):
    return (df
        .transform(rename_columns)
        .transform(filter_invalid_age)
        .transform(clean_monthly_income)
        .transform(clean_number_of_dependents))

# COMMAND ----------

def add_total_late_payments(df):
    return df.withColumn(
        "total_late_payments",
        F.col("times_30_59_days_late") + F.col("times_60_89_days_late") + F.col("times_90_days_late"),
    )


def add_max_delinquency_severity(df):
    return df.withColumn(
        "max_delinquency_severity",
        F.when(F.col("times_90_days_late") > 0, 3)
         .when(F.col("times_60_89_days_late") > 0, 2)
         .when(F.col("times_30_59_days_late") > 0, 1)
         .otherwise(0),
    )


def add_credit_lines_per_dependent(df):
    return df.withColumn(
        "credit_lines_per_dependent",
        F.col("open_credit_lines") / (F.col("number_of_dependents") + 1),
    )


def build_features(df):
    return (df
        .transform(add_total_late_payments)
        .transform(add_max_delinquency_severity)
        .transform(add_credit_lines_per_dependent))

# COMMAND ----------

df_features = build_features(clean_pipeline(df))

(df_features.write
    .mode("overwrite")
    .saveAsTable("workspace.default.client_features"))

print("Lignes dans client_features :", spark.table("workspace.default.client_features").count())

# COMMAND ----------

import mlflow
import mlflow.lightgbm
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score

pdf = spark.table("workspace.default.client_features").orderBy("customer_id").toPandas()

X = pdf.drop(columns=["customer_id", "target"])
y = pdf["target"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

ratio = (y_train == 0).sum() / (y_train == 1).sum()
params = {"scale_pos_weight": float(ratio), "random_state": 42, "verbose": -1}

with mlflow.start_run(run_name="lightgbm_pipeline"):
    mlflow.log_params(params)
    mlflow.log_param("n_train", len(X_train))

    model = LGBMClassifier(**params)
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    roc_auc = roc_auc_score(y_test, proba)
    pr_auc = average_precision_score(y_test, proba)

    mlflow.log_metric("roc_auc", roc_auc)
    mlflow.log_metric("pr_auc", pr_auc)
    mlflow.lightgbm.log_model(model, name="model", input_example=X_train.head(5))

print(f"ROC-AUC : {roc_auc:.4f} | PR-AUC : {pr_auc:.4f}")