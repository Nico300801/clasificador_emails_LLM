"""Usage (CLI)
-----------
    python -m src.pipeline                 # pesos normales
    python -m src.pipeline --top 5         # solo los 5 primeros
"""

import argparse
import json
import logging
import sys
import os
from typing import Optional, List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ingest       import fetch_emails
from src.cleaner      import clean_emails
from src.llm_analyzer import analyse_emails
from src.scoring      import score_emails, ScoringWeights

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")


def run_pipeline(
    api_url: str = "http://localhost:8000",
    weights: Optional[ScoringWeights] = None,
) -> List[Dict]:

    logger.info("── Paso 1: Ingesta de emails ──────────────────────────")
    raw_emails = fetch_emails(api_url)
    logger.info("Se han obtenido %d emails.", len(raw_emails))

    logger.info("── Paso 2: Limpiando emails ───────────────────────────")
    clean = clean_emails(raw_emails)

    logger.info("── Paso 3: Analizando con LLM ────────────────────────")
    analysed = analyse_emails(clean)

    logger.info("── Paso 4: Puntuación y clasificación ─────────────────────────")
    scored = score_emails(analysed, weights)

    logger.info("Pipeline completado. %d emails calificados.", len(scored))
    return scored


def _print_results(emails: List[Dict], top: Optional[int] = None):
    subset = emails[:top] if top else emails
    print("\n" + "═" * 65)
    print(f"  📬  COLA DE PRIORIDAD DE EMAIL (showing {len(subset)}/{len(emails)})")
    print("═" * 65)
    for rank, email in enumerate(subset, start=1):
        analysis = email.get("analysis", {})
        print(
            f"\n#{rank:02d}  [{email['urgency_score']:5.1f}/100]  {email['subject'][:55]}"
        )
        print(
            f"     From : {email['from']}"
        )
        print(
            f"     Tema: {analysis.get('topic','?'):18s}  "
            f"Sentimiento: {analysis.get('sentiment','?'):10s}  "
            f"Confianza: {analysis.get('confidence', 0):.0%}"
        )
        print(f"     💬  {analysis.get('summary', '—')}")
    print("\n" + "═" * 65 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de priorización de correo electrónico")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--top", type=int, default=None, help="Mostrar solo los N mejores resultados")
    args = parser.parse_args()

    results = run_pipeline(api_url=args.api_url)
    _print_results(results, top=args.top)
