import sys
import os
import time

import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ingest       import fetch_emails
from src.cleaner      import clean_emails
from src.llm_analyzer import analyse_emails
from src.scoring      import score_emails, ScoringWeights

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="📬 Cola de prioridad de emails",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS para la página

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }
    .stApp { background-color: #0d0f14; color: #e2e8f0; }
    .badge-critical { background:#ef4444; color:white; padding:2px 10px; border-radius:4px; font-weight:700; font-size:0.75rem; }
    .badge-high     { background:#f97316; color:white; padding:2px 10px; border-radius:4px; font-weight:700; font-size:0.75rem; }
    .badge-medium   { background:#eab308; color:#000;  padding:2px 10px; border-radius:4px; font-weight:700; font-size:0.75rem; }
    .badge-low      { background:#22c55e; color:white; padding:2px 10px; border-radius:4px; font-weight:700; font-size:0.75rem; }
    .email-card {
        background: #161a24;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .score-num {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 2rem;
        font-weight: 600;
        color: #60a5fa;
    }
    .meta-tag { color: #94a3b8; font-size: 0.82rem; }
    .summary-text { color: #cbd5e1; font-style: italic; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)


def urgency_badge(score: float) -> str:
    if score >= 75:
        return '<span class="badge-critical">CRITICAL</span>'
    elif score >= 55:
        return '<span class="badge-high">HIGH</span>'
    elif score >= 35:
        return '<span class="badge-medium">MEDIUM</span>'
    else:
        return '<span class="badge-low">LOW</span>'


def sentiment_emoji(sentiment: str) -> str:
    return {"negative": "😡", "neutral": "😐", "positive": "😊"}.get(sentiment, "❓")


@st.cache_data(show_spinner=False)
def load_and_analyse(api_url: str) -> list[dict]:
    raw      = fetch_emails(api_url)
    cleaned  = clean_emails(raw)
    analysed = analyse_emails(cleaned)
    return analysed


# Barra lateral

with st.sidebar:
    st.markdown("## ⚙️ Configuración")
    api_url = st.text_input("API URL", value="http://localhost:8000")

    if st.button("🔄 Actualizar y analizar otra vez", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("## 🎚️ Pesos de urgencia.")
    st.caption("Ajusta la importancia de cada factor. Deben sumar 1.0.")

    w_sentiment  = st.slider("😡 Sentimiento",   0.0, 1.0, 0.30, 0.05)
    w_topic      = st.slider("🏷️ Tema",        0.0, 1.0, 0.30, 0.05)
    w_recency    = st.slider("⏰ Frescura",       0.0, 1.0, 0.20, 0.05)
    w_unread     = st.slider("📨 Bonus sin leer",  0.0, 1.0, 0.10, 0.05)
    w_confidence = st.slider("🤖 Confianza del LLM",0.0, 1.0, 0.10, 0.05)

    total = round(w_sentiment + w_topic + w_recency + w_unread + w_confidence, 2)
    if abs(total - 1.0) > 0.001:
        st.warning(f"⚠️ Los pesos suman **{total}** (debe ser 1.0). Normalizando…")
        factor = 1.0 / total if total > 0 else 1.0
        w_sentiment  *= factor
        w_topic      *= factor
        w_recency    *= factor
        w_unread     *= factor
        w_confidence *= factor

    st.markdown("---")
    st.markdown("### 📖 Peso racional")
    st.markdown("""
| Factor | Why it matters |
|--------|---------------|
| Sentiment | Negative → frustrated user |
| Topic | Bugs/complaints = direct impact |
| Recency | Fresh emails need faster response |
| Unread | Not seen yet → higher urgency |
| Confidence | Low-confidence analysis → down-weighted |
""")


# Contenido principal

st.markdown("# 📬 Cola de emails prioritarios")
st.markdown("Clasificación de pacientes en tiempo real mediante análisis LLM + puntuación de urgencia configurable.")

# Load data
with st.spinner("Conectando a la API y ejecutando análisis de LLM …"):
    try:
        analysed = load_and_analyse(api_url)
    except RuntimeError as e:
        st.error(str(e))
        st.stop()

# Apply weights
weights = ScoringWeights(
    sentiment=w_sentiment,
    topic=w_topic,
    recency=w_recency,
    unread=w_unread,
    confidence=w_confidence,
)
ranked = score_emails(analysed, weights)

# Resumen de métricas

col1, col2, col3, col4 = st.columns(4)
col1.metric("Emails totales",    len(ranked))
col2.metric("Crítico (≥75)",  sum(1 for e in ranked if e["urgency_score"] >= 75))
col3.metric("Alto (55–74)",    sum(1 for e in ranked if 55 <= e["urgency_score"] < 75))
col4.metric("No leído",          sum(1 for e in ranked if "UNREAD" in e.get("labels", [])))

st.markdown("---")


tab_queue, tab_table, tab_breakdown = st.tabs(["📋 Cola de prioridad", "📊 Tabla de datos", "🔬 Desglose de puntuación"])

with tab_queue:
    for rank, email in enumerate(ranked, start=1):
        analysis  = email.get("analysis", {})
        score     = email["urgency_score"]
        breakdown = email.get("score_breakdown", {})

        with st.container():
            st.markdown(f"""
<div class="email-card">
  <div style="display:flex; justify-content:space-between; align-items:flex-start;">
    <div>
      <span style="color:#94a3b8; font-size:0.8rem;">#{rank:02d}</span>&nbsp;
      {urgency_badge(score)}&nbsp;
      <strong style="font-size:1.05rem;">{email['subject']}</strong>
    </div>
    <div class="score-num">{score:.1f}</div>
  </div>
  <div class="meta-tag" style="margin-top:6px;">
    {sentiment_emoji(analysis.get('sentiment','?'))} {analysis.get('sentiment','?').capitalize()} &nbsp;|&nbsp;
    🏷️ {analysis.get('topic','?').replace('_',' ').title()} &nbsp;|&nbsp;
    📧 {email['from']} &nbsp;|&nbsp;
    📅 {email.get('date','')[:16]}
    {"&nbsp;|&nbsp; 🔵 UNREAD" if "UNREAD" in email.get("labels",[]) else ""}
  </div>
  <div class="summary-text">💬 {analysis.get('summary','—')}</div>
</div>
""", unsafe_allow_html=True)

            with st.expander(f"Details & clean body — {email['id']}"):
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.markdown("**Score breakdown**")
                    bd_df = pd.DataFrame(
                        list(breakdown.items()),
                        columns=["Factor", "Points"],
                    )
                    st.dataframe(bd_df, use_container_width=True, hide_index=True)
                with c2:
                    st.markdown("**Cleaned body**")
                    st.text_area(
                        "", email.get("clean_body", email.get("body", "")),
                        height=160, key=f"body_{email['id']}", disabled=True
                    )

with tab_table:
    table_data = []
    for email in ranked:
        a = email.get("analysis", {})
        table_data.append({
            "Rank":       ranked.index(email) + 1,
            "Score":      email["urgency_score"],
            "Subject":    email["subject"][:55],
            "From":       email["from"],
            "Sentiment":  a.get("sentiment", "?"),
            "Topic":      a.get("topic", "?"),
            "Confidence": f"{a.get('confidence', 0):.0%}",
            "Unread":     "✓" if "UNREAD" in email.get("labels", []) else "",
        })
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

with tab_breakdown:
    st.markdown("### How each factor contributes to the final score")
    breakdown_rows = []
    for email in ranked:
        bd = email.get("score_breakdown", {})
        breakdown_rows.append({
            "Subject": email["subject"][:40],
            "Sentiment pts": bd.get("sentiment_score", 0),
            "Topic pts":     bd.get("topic_score", 0),
            "Recency pts":   bd.get("recency_score", 0),
            "Unread pts":    bd.get("unread_score", 0),
            "Confidence pts":bd.get("confidence_score", 0),
            "TOTAL":         email["urgency_score"],
        })
    st.dataframe(pd.DataFrame(breakdown_rows), use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Pipeline: FastAPI mock → Regex cleaner → Ollama (gemma3:1b) → Urgency scoring → Streamlit UI")
