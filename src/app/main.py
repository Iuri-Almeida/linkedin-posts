import time
import httpx
import secrets
import urllib.parse

from fastapi import (
    FastAPI,
    HTTPException
)
from fastapi.responses import RedirectResponse
from jose import jwt
from datetime import (
    datetime,
    timezone
)

from app.utils.provider import (
    get_settings,
    get_repository,
    get_client
)
from app.domain.models.post import Post

app = FastAPI(title="LinkedIn Poster API")

settings = get_settings()
token_repository = get_repository()
linkedin_client = get_client()

STATE_STORE = dict()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.SERVICE_NAME,
        "ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
    }


@app.get("/env-check")
def env_check():
    return {
        "client_id_set": bool(settings.LI_CLIENT_ID),
        "redirect_uri": settings.LI_REDIRECT_URI
    }


@app.get("/auth/login")
def login():
    state = secrets.token_urlsafe(32)
    STATE_STORE[state] = time.time() + 600

    params = {
        "response_type": "code",
        "client_id": settings.LI_CLIENT_ID,
        "redirect_uri": settings.LI_REDIRECT_URI,
        "scope": settings.LI_SCOPES,
        "state": state,
    }

    return RedirectResponse(f"{settings.LI_AUTH_URL}?{urllib.parse.urlencode(params)}")


@app.get("/auth/callback")
def callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None
):
    if error:
        raise HTTPException(status_code=400, detail={"oauth_error": error, "description": error_description})

    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' param.")

    if state in STATE_STORE and STATE_STORE[state] > time.time():
        print("Deleting state after validation")
        del STATE_STORE[state]

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.LI_REDIRECT_URI,
            "client_id": settings.LI_CLIENT_ID,
            "client_secret": settings.LI_CLIENT_SECRET,
        }

        with httpx.Client(timeout=20) as c:
            r = c.post(settings.LI_TOKEN_URL, data=data)

        if r.status_code >= 400:
            raise HTTPException(
                status_code=r.status_code,
                detail={
                    "status": r.status_code,
                    "error": r.text
                }
            )

        token: dict = r.json()

        token_bundle = token_repository.get()

        token_bundle.access_token = token.get("access_token")
        token_bundle.expires_at = time.time() + token.get("expires_in", 3600)
        token_bundle.refresh_token = token.get("refresh_token")

        id_token = token.get("id_token")

        if not token_bundle.is_valid:
            raise HTTPException(status_code=400, detail="No 'access_token' was returned.")

        if not id_token:
            raise HTTPException(status_code=400, detail="No 'id_token' was returned. Ensure 'openid profile email' scope is granted.")

        claims = jwt.get_unverified_claims(id_token)

        sub = claims.get("sub")

        if not sub:
            raise HTTPException(status_code=400, detail="ID Token missing 'sub' claim.")

        token_bundle.person_urn = f"urn:li:person:{sub}"

        token_repository.set(token_bundle)

        return {"message": "LinkedIn connected", "author": token_bundle.person_urn}

    raise HTTPException(status_code=400, detail="Invalid or expired 'state' (CSRF protection).")


@app.get("/auth/status")
def auth_status():
    token_bundle = linkedin_client.refresh_if_needed()

    return {
        "logged_in": bool(token_bundle.access_token),
        "has_refresh": bool(token_bundle.refresh_token),
        "expires_in_s": max(0, int(token_bundle.expires_at - time.time())),
        "author": token_bundle.person_urn,
    }


@app.post("/posts")
def posts(post: Post):
    token_bundle = linkedin_client.refresh_if_needed()

    if not token_bundle.person_urn:
        raise HTTPException(status_code=400, detail="No 'person_urn' was found. Please make sure to login.")

    return linkedin_client.create_text_post(post)
