"""
dashboard.py

Dashboard de monitoring du modèle de scoring crédit.
Compare les données de référence (entraînement) aux données actuelles
(simulées, représentant un flux de production) et affiche l'état du drift.

Lancer avec : streamlit run monitoring/dashboard.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import numpy as np
from evidently import Report
from evidently.presets import DataDriftPreset

from scoring_lib.preprocessing import clean_pipeline
from scoring_lib.features import build_features

st.set_page_config(page_title="Monitoring - Scoring Crédit", layout="wide")

st.title("📊 Monitoring du Modèle de Scoring Crédit")
st.markdown("Surveillance du data drift entre les données d'entraînement et les données actuelles.")


@st.cache_data
def load_reference_data():
    """Charge et prépare les données de référence (entraînement)."""
    df = pd.read_csv("data/cs-training.csv")
    df = clean_pipeline(df)
    df["debt_ratio"] = df["debt_ratio"].clip(upper=5)
    df = build_features(df)
    return df


@st.cache_data
def simulate_current_data(df_reference):
    """Simule des données actuelles avec un drift artificiel (démo)."""
    df_current = df_reference.copy()
    np.random.seed(42)
    df_current["monthly_income_raw"] = df_current["monthly_income_raw"] * np.random.uniform(0.7, 0.9, size=len(df_current))
    df_current["debt_ratio"] = df_current["debt_ratio"] * np.random.uniform(1.1, 1.3, size=len(df_current))
    df_current["age"] = (df_current["age"] * np.random.uniform(0.8, 0.95, size=len(df_current))).astype(int)
    return df_current


with st.spinner("Chargement des données..."):
    df_reference = load_reference_data()
    df_current = simulate_current_data(df_reference)

columns_to_check = [col for col in df_reference.columns if col not in ["customer_id", "target"]]

report = Report(metrics=[DataDriftPreset()])
result = report.run(
    reference_data=df_reference[columns_to_check],
    current_data=df_current[columns_to_check],
)

result_dict = result.dict()

# Extraction des métriques principales pour l'affichage
drift_summary = result_dict["metrics"][0]
n_drifted = drift_summary["value"]["count"]
share_drifted = drift_summary["value"]["share"]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Colonnes surveillées", len(columns_to_check))

with col2:
    st.metric("Colonnes en drift", n_drifted)

with col3:
    color = "🔴" if share_drifted >= 0.5 else "🟡" if share_drifted >= 0.2 else "🟢"
    st.metric(f"{color} Part des colonnes driftées", f"{share_drifted:.1%}")

st.markdown("---")
st.subheader("Détail par variable")

# Reconstruction d'un tableau lisible à partir du résultat Evidently
drift_rows = []
for metric in result_dict["metrics"][1:]:
    if "column" in metric.get("metric_id", ""):
        drift_rows.append(metric)

if drift_rows:
    st.write("Consultez le rapport détaillé ci-dessous pour l'analyse complète par variable.")

st.markdown("---")
st.subheader("Rapport complet")
result.save_html("temp_report.html")
with open("temp_report.html", "r", encoding="utf-8") as f:
    html_content = f.read()
st.components.v1.html(html_content, height=800, scrolling=True)