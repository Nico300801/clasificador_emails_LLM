import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

from src.pipeline import run_pipeline, _print_results


def main():
    print("\n📬  Pipeline de priorización de correo electrónico")
    print("──────────────────────────────────────────────────────────")
    print("Asegúrate de que el servidor FastAPI está funcionando:")
    print("  uvicorn src.api:app --reload\n")

    try:
        results = run_pipeline()
        _print_results(results)
    except RuntimeError as e:
        print(f"\n❌  Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
