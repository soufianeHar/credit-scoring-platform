"""
chat_ui.py

Interface de chat pour l'agent Talk-to-Data.
Lancer avec : streamlit run agent/chat_ui.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from agent.agent import ask, DEFAULT_MODEL

st.set_page_config(page_title="Talk-to-Data — Scoring Crédit", page_icon="💳", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0d1117; }
[data-testid="stHeader"] { background-color: rgba(0,0,0,0); }

.hero-title {
    font-size: 2.1rem; font-weight: 800; color: #f0f6fc;
    margin-bottom: 0.2rem; letter-spacing: -0.02em;
}
.hero-subtitle { color: #8b949e; font-size: 1rem; margin-bottom: 1.6rem; }

.metric-box {
    background: #161b22; border: 1px solid #30363d; border-radius: 10px;
    padding: 1rem 1.2rem; text-align: center;
}
.metric-box .value { font-size: 1.7rem; font-weight: 700; color: #58a6ff; }
.metric-box .label { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.2rem; }

.result-card {
    background: #161b22; border: 1px solid #30363d; border-radius: 10px;
    padding: 1.1rem 1.3rem; margin-bottom: 1rem;
}
.question-badge {
    display: inline-block; background: #1f6feb26; color: #79c0ff;
    padding: 0.25rem 0.8rem; border-radius: 999px; font-size: 0.85rem; margin-bottom: 0.7rem;
}
.footer-note { color: #484f58; font-size: 0.8rem; text-align: center; margin-top: 2rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-title">💳 Talk-to-Data — Scoring Crédit</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Posez une question en français sur les 149 999 clients scorés. '
    'L\'agent écrit une requête SQL BigQuery, validée avant exécution.</div>',
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []

col_model, col_reset = st.columns([3, 1])
with col_model:
    model = st.selectbox(
        "Modèle",
        ["qwen2.5-coder:3b", "qwen2.5-coder:7b"],
        index=0 if DEFAULT_MODEL == "qwen2.5-coder:3b" else 1,
    )
with col_reset:
    st.write("")
    if st.button("🗑️ Effacer l'historique", use_container_width=True):
        st.session_state.history = []
        st.rerun()

question = st.chat_input("Votre question sur les clients...")
if question:
    with st.spinner("L'agent réfléchit..."):
        result = ask(question, model=model)
    st.session_state.history.append(result)
    
n_questions = len(st.session_state.history)
n_success = sum(1 for r in st.session_state.history if r["error"] is None)
success_rate = f"{round(100 * n_success / n_questions)}%" if n_questions else "—"

c1, c2, c3 = st.columns(3)
for col, value, label in [
    (c1, n_questions, "Questions posées"),
    (c2, success_rate, "Taux de réussite"),
    (c3, model, "Modèle actif"),
]:
    with col:
        st.markdown(f'<div class="metric-box"><div class="value">{value}</div>'
                     f'<div class="label">{label}</div></div>', unsafe_allow_html=True)

st.write("")

EXAMPLES = [
    "Quel est le score moyen des clients de moins de 30 ans ?",
    "Quel est le taux de défaut réel des clients dont le score dépasse 0.8 ?",
    "Quels sont les 5 clients avec le score de risque le plus élevé ?",
]
st.caption("Exemples :  " + "   •   ".join(EXAMPLES))



def render_result(result: dict) -> None:
    st.markdown(f'<span class="question-badge">💬 {result["question"]}</span>', unsafe_allow_html=True)

    if result["error"]:
        st.error(f"Échec après {result['attempts']} essai(s) : {result['error']}")
    else:
        data = result["data"]
        if isinstance(data, pd.DataFrame) and "risk_score" in data.columns:
            display_df = data.copy()
            display_df["niveau"] = display_df["risk_score"].apply(
                lambda s: "🟢 Faible" if s < 0.33 else ("🟠 Moyen" if s < 0.66 else "🔴 Élevé")
            )
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(data, use_container_width=True, hide_index=True)

    if result["sql"]:
        with st.expander("🔍 Voir la requête SQL générée et validée"):
            st.code(result["sql"], language="sql")
            st.caption(f"{result['attempts']} essai(s) avant exécution réussie")


for result in reversed(st.session_state.history):
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    render_result(result)
    st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.history:
    st.info("👋 Posez une question ci-dessus pour commencer, ou cliquez sur un des exemples suggérés.")

st.markdown(
    '<p class="footer-note">Chaque requête SQL est validée (SELECT seul, table unique) avant exécution sur BigQuery.</p>',
    unsafe_allow_html=True,
)