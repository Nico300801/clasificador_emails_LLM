import requests
import logging

logger = logging.getLogger(__name__)

DEFAULT_API_URL = "http://localhost:8000"


def fetch_emails(api_url: str = DEFAULT_API_URL) -> list[dict]:

    endpoint = f"{api_url.rstrip('/')}/emails"
    try:
        resp = requests.get(endpoint, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        emails = data.get("emails", [])
        logger.info("Fetched %d emails from %s", len(emails), endpoint)
        return emails
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"No se puede conectar a la API en {endpoint}. "
            "Asegúrate de que el servidor FastAPI está funcionando: "
            "`uvicorn src.api:app --reload`"
        )
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"API ha devuelto un error: {e}")
