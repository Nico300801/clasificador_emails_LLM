# 📬 Pipeline de Priorización de Emails

> **Máster Digitech FP — Proyecto práctico**  
> Clasificación y orden automático de correos de soporte entrantes usando análisis con LLM local y una fórmula configurable de urgencia.

---

## 🏗️ Arquitectura

```
Emails en bruto (API mock)
        │
        ▼
┌─────────────────┐
│   FastAPI       │  src/api.py  — expone emails simulados vía HTTP
│   Servidor Mock │
└────────┬────────┘
         │ HTTP GET /emails
         ▼
┌─────────────────┐
│   Ingesta       │  src/ingest.py  — obtiene emails desde la API
└────────┬────────┘
         ▼
┌─────────────────┐
│   Limpieza      │  src/cleaner.py  — elimina HTML, citas, PII (regex)
└────────┬────────┘
         ▼
┌─────────────────┐
│ Analizador LLM  │  src/llm_analyzer.py  — Ollama (gemma3:1b) o fallback Claude
│ sentimiento     │  extrae: sentimiento · tema · resumen · confianza
│ tema            │
└────────┬────────┘
         ▼
┌─────────────────┐
│   Scoring       │  src/scoring.py  — fórmula de urgencia con pesos configurables
└────────┬────────┘
         ▼
┌─────────────────┐
│   Dashboard     │  src/dashboard.py  — interfaz Streamlit con sliders en vivo
└─────────────────┘
```

---

## 📁 Estructura del repositorio

```
📂 src/
    ├── api.py              # FastAPI con emails simulados
    ├── cleaner.py          # Limpieza de emails basada en regex
    ├── llm_analyzer.py     # Análisis con Ollama, modelo local Gemma3:1b
    ├── scoring.py          # Fórmula de puntuación de urgencia
    ├── pipeline.py         # Orquestación completa del pipeline
    ├── dashboard.py        # Interfaz Streamlit
    └── ingest.py           # Ingesta de emails desde la API

📂 data/
    ├── emails.py           
    ├── mock_emails.json    # Dataset MOCK_EMAILS (10 emails)

📄 main.py                  # Punto de entrada CLI
📄 requirements.txt
📄 README.md
```

---

## 🚀 Inicio rápido

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. (Recomendado) Instalar Ollama, descargar el modelo y ejecutarlo

```bash
# Install Ollama — https://ollama.com
irm https://ollama.com/install.ps1 | iex

ollama pull gemma3:1b

ollama run gemma3:1
```

### 3. Iniciar el servidor de la API mock

```bash
uvicorn src.api:app --reload --port 8000
```

Comprobar en: http://localhost:8000/emails

### 4a. Ejecutar el pipeline desde CLI

```bash
python main.py
# o
python -m src.pipeline --top 5
```

### 4b. Lanzar el dashboard en Streamlit

```bash
streamlit run src/dashboard.py
```

---

## 🧮 Fórmula de puntuación de urgencia

```
urgency_score = (
    w_sentiment  × sentiment_score  +
    w_topic      × topic_score      +
    w_recency    × recency_score    +
    w_unread     × unread_bonus     +
    w_confidence × confidence_boost
) × 100
```

### Pesos por defecto

| Factor | Weight | Rationale |
|--------|--------|-----------|
| **Sentiment** | 0.30 | Negative sentiment → frustrated user who needs immediate attention |
| **Topic** | 0.30 | Bugs and complaints have direct business impact |
| **Recency** | 0.20 | Older emails decay in urgency (linear decay over 7 days) |
| **Unread** | 0.10 | Emails not yet seen by any agent get a priority boost |
| **LLM confidence** | 0.10 | Low-confidence predictions are down-weighted to avoid mis-triage |

### Valores de puntuación por componente

**Sentimiento:**
- `negative` → 1.0 | `neutral` → 0.4 | `positive` → 0.1

**Tema:**
- `complaint` → 1.00 | `bug_report` → 0.95 | `billing` → 0.80
- `follow_up` → 0.65 | `sales_inquiry` → 0.55 | `feature_request` → 0.35
- `partnership` → 0.30 | `other` → 0.20

### Demo con sliders en vivo

El dashboard de Streamlit permite modificar cualquier peso en tiempo real y ver cómo cambia el ranking al instante — mostrando cómo distintas prioridades de negocio generan diferentes colas.

---

## 🧹 Pipeline de limpieza (regex)

`cleaner.py` aplica las siguientes transformaciones en orden:

1. Elimina etiquetas y entidades HTML
2. Elimina encabezados de mensajes reenviados
3. Elimina encabezados de respuesta ("On Mon, ... wrote:")
4. Elimina líneas citadas (`> ...`)
5. Elimina firmas y disclaimers legales
6. Oculta datos personales: teléfonos → `[PHONE]`, emails → `[EMAIL]`, URLs → `[URL]`
7. Normaliza espacios en blanco

---

## 🤖 Análisis con LLM

El analizador envía un prompt estructurado al modelo local de Ollama (`gemma3:1b`) y espera una respuesta JSON con:

```json
{
  "sentiment":  "negative",
  "topic":      "complaint",
  "summary":    "Customer demands refund for non-working service.",
  "confidence": 0.92
}
```

## 📦 Dependencias

```
fastapi
uvicorn[standard]
streamlit
pandas
requests
```
