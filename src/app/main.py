import secrets
import urllib.parse

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from datetime import datetime

from app.utils.provider import get_settings

app = FastAPI(title="LinkedIn Poster API")
settings = get_settings()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.SERVICE_NAME,
        "ts": datetime.now()
    }


@app.get("/env-check")
def env_check():
    return {
        "client_id_set": bool(settings.LI_CLIENT_ID),
        "redirect_uri": settings.LI_REDIRECT_URI
    }


@app.get("/auth/login")
def login():
    params = {
        "response_type": "code",
        "client_id": settings.LI_CLIENT_ID,
        "redirect_uri": settings.LI_REDIRECT_URI,
        "scope": settings.LI_SCOPES,
        "state": secrets.token_urlsafe(32),
    }

    return RedirectResponse(f"{settings.LI_AUTH_URL}?{urllib.parse.urlencode(params)}")
