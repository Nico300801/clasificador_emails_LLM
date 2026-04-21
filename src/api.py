from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.emails import MOCK_EMAILS

app = FastAPI(
    title="Email Mock API",
    description="API local que simula la bandeja de entrada de Gmail para el proceso de priorización.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/emails", summary="Listar todos los emails")
def get_emails():
    """Return all emails from the mock inbox."""
    return MOCK_EMAILS


@app.get("/emails/{email_id}", summary="Recibe un único correo electrónico por ID")
def get_email(email_id: str):
    for email in MOCK_EMAILS["emails"]:
        if email["id"] == email_id:
            return email
    raise HTTPException(status_code=404, detail=f"Email '{email_id}' no encontrado.")


@app.get("/health", summary="Comprobando estado")
def health():
    return {"status": "ok", "emails_count": len(MOCK_EMAILS["emails"])}
