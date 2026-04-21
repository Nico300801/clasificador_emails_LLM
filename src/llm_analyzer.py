import json
import re
import requests
import os
import logging

logger = logging.getLogger(__name__)

# Configuración de Ollama

OLLAMA_URL  = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")

ANALYSIS_PROMPT = """\
You are an email triage assistant. Analyse the following email and respond ONLY with a valid JSON object — no markdown, no extra text.

Email subject: {subject}
Email body:
{body}

Respond with exactly this JSON structure:
{{
  "sentiment": "<positive|neutral|negative>",
  "topic": "<complaint|bug_report|feature_request|billing|sales_inquiry|partnership|follow_up|other>",
  "summary": "<one-sentence summary, max 20 words>",
  "confidence": <float between 0.0 and 1.0>
}}
"""

#

def _extract_json(text: str) -> dict:
    text = text.strip()
    # Eliminar posibles bloques de código Markdown (```json ... ```) que Ollama podría incluir
    text = re.sub(r"```(?:json)?", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No se ha encontrado ningún objeto de JSON en la respuesta del LLM: {text!r}")
    return json.loads(match.group())


def _call_ollama(subject: str, body: str) -> dict:
    prompt = ANALYSIS_PROMPT.format(subject=subject, body=body)
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
    resp.raise_for_status()
    raw = resp.json().get("response", "")
    return _extract_json(raw)

# API principal

def analyse_email(email: dict) -> dict:
    subject   = email.get("subject", "")
    body      = email.get("clean_body", email.get("body", ""))

    analysis  = None
    backend   = "ollama"

    try:
        analysis = _call_ollama(subject, body)
        logger.info("Analizado %s via Ollama", email["id"])
    except Exception as ollama_err:
        logger.error("Ollama ha dado un error por %s: %s", email["id"], ollama_err)
        analysis = {
        "sentiment":  "neutral",
        "topic":      "other",
        "summary":    "Analysis unavailable.",
        "confidence": 0.0,
    }
    backend = "error"

    result = dict(email)
    result["analysis"] = analysis
    result["analysis_backend"] = backend
    return result


def analyse_emails(emails: list[dict]) -> list[dict]:
    return [analyse_email(e) for e in emails]
