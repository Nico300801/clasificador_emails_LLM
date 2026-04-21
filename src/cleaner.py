import re


# Eliminar HTML, bloques de código, líneas citadas, firmas, datos personales, etc. para obtener un texto limpio y adecuado para el análisis LLM.

_HTML_TAGS     = re.compile(r"<[^>]+>")
_HTML_ENTITIES = re.compile(r"&[a-zA-Z]+;|&#?\d+;")

# Líneas en las respuestas de email que comienzan con ">" (citas de emails anteriores)
_QUOTED_LINES  = re.compile(r"^>.*$", re.MULTILINE)

# Reply headers típicos en respuestas de email ("On Mon, Jan 1, 2020 at 12:00 PM ... wrote:")
_REPLY_HEADER  = re.compile(
    r"On\s+\w{3},\s+\w{3}\s+\d{1,2},\s+\d{4}.*wrote:\s*", re.IGNORECASE | re.DOTALL
)

# Encabezados de mensajes reenviados
_FWD_HEADER    = re.compile(
    r"-{5,}\s*Forwarded message\s*-{5,}.*?(?=\n\n|\Z)", re.IGNORECASE | re.DOTALL
)

# Firmas
_SIGNATURE     = re.compile(
    r"(^--\s*$|Sent from my \w+.*|This email and any attachments.*)", re.MULTILINE | re.IGNORECASE
)

# Datos personales
_PHONE         = re.compile(r"\+?[\d\s\(\)\-]{7,15}")
_EMAIL_ADDR    = re.compile(r"[\w.\-+]+@[\w.\-]+\.\w{2,}")
_URL           = re.compile(r"https?://\S+|www\.\S+")

# Líneas en blanco
_BLANK_LINES   = re.compile(r"\n{3,}")


def clean_email(raw_body: str) -> str:
    text = raw_body

    # 1. Quitar HTML
    text = _HTML_TAGS.sub(" ", text)
    text = _HTML_ENTITIES.sub(" ", text)

    # 2. Eliminar bloques de mensajes reenviados
    text = _FWD_HEADER.sub("", text)

    # 3. Eliminar encabezados de respuesta
    text = _REPLY_HEADER.sub("", text)

    # 4. Eliminar líneas de respuesta entre comillas ("> ...")
    text = _QUOTED_LINES.sub("", text)

    # 5. Eliminar firmas y descargos de responsabilidad
    text = _SIGNATURE.sub("", text)

    # 6. Redactar datos personales
    text = _PHONE.sub("[PHONE]", text)
    text = _EMAIL_ADDR.sub("[EMAIL]", text)
    text = _URL.sub("[URL]", text)

    # 7. Normalizar espacios en blanco
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _BLANK_LINES.sub("\n\n", text)
    text = text.strip()

    return text


def clean_emails(emails: list[dict]) -> list[dict]:
    cleaned = []
    for email in emails:
        copy = dict(email)
        copy["clean_body"] = clean_email(email.get("body", ""))
        cleaned.append(copy)
    return cleaned
