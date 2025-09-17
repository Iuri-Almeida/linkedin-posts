import httpx
import time
import urllib.parse

from fastapi import HTTPException
from jose import jwt
from typing import Any

from app.config.settings import Settings
from app.domain.models.post import Post
from app.domain.models.token import Token
from app.domain.repository.token_repository import TokenRepository


class LinkedInClient:
    def __init__(self, settings: Settings, repository: TokenRepository):
        self.__settings = settings
        self.repository = repository

    def build_authorize_url(self, state: str = "abc123") -> str:
        params = {
            "response_type": "code",
            "client_id": self.__settings.LI_CLIENT_ID,
            "redirect_uri": self.__settings.LI_REDIRECT_URI,
            "scope": self.__settings.LI_SCOPES,
            "state": state,
        }

        return f"{self.__settings.LI_AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code: str) -> Token:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.__settings.LI_REDIRECT_URI,
            "client_id": self.__settings.LI_CLIENT_ID,
            "client_secret": self.__settings.LI_CLIENT_SECRET,
        }

        with httpx.Client(timeout=20) as c:
            r = c.post(self.__settings.LI_TOKEN_URL, data=data)

        if r.status_code >= 400:
            raise HTTPException(
                status_code=r.status_code,
                detail={
                    "status": r.status_code,
                    "error": r.text
                }
            )

        token = r.json()

        token_bundle = self.repository.get()
        token_bundle.access_token  = token["access_token"]
        token_bundle.expires_at    = time.time() + token.get("expires_in", 3600)
        token_bundle.refresh_token = token.get("refresh_token")

        id_token = token.get("id_token")

        if not id_token:
            raise ValueError("No id_token returned; ensure 'openid profile email' scope is granted")

        claims = jwt.get_unverified_claims(id_token)

        sub = claims.get("sub")

        if not sub:
            raise ValueError("ID token missing 'sub' claim")

        token_bundle.person_urn = f"urn:li:person:{sub}"

        self.repository.set(token_bundle)

        return token_bundle

    def refresh_if_needed(self) -> Token:
        token_bundle = self.repository.get()

        if time.time() < token_bundle.expires_at - 60:
            return token_bundle

        if not token_bundle.refresh_token:
            raise HTTPException(status_code=401, detail="Token expired and no refresh_token available.")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": token_bundle.refresh_token,
            "client_id": self.__settings.LI_CLIENT_ID,
            "client_secret": self.__settings.LI_CLIENT_SECRET,
        }

        with httpx.Client(timeout=20) as c:
            r = c.post(self.__settings.LI_TOKEN_URL, data=data)

        if r.status_code >= 400:
            raise HTTPException(
                status_code=r.status_code,
                detail={"error": r.text}
            )

        payload = r.json()

        token_bundle.access_token = payload["access_token"]
        token_bundle.expires_at   = time.time() + payload.get("expires_in", 3600)

        if "refresh_token" in payload:
            token_bundle.refresh_token = payload["refresh_token"]

        self.repository.set(token_bundle)

        return token_bundle

    def get_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": self.__settings.LINKEDIN_VERSION,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def create_text_post(self, post: Post) -> dict[str, Any]:
        token_bundle = self.refresh_if_needed()

        payload = {
            "author": token_bundle.person_urn,
            "commentary": post.text,
            "visibility": post.visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
        }

        with httpx.Client(timeout=20) as c:
            r = c.post(self.__settings.LI_POSTS_URL, headers=self.get_headers(token_bundle.access_token), json=payload)

        if r.status_code >= 400:
            return HTTPException(status_code=r.status_code, headers=dict(r.headers), detail={"body": r.text})

        ct = (r.headers.get("content-type") or "").lower()

        if "application/json" in ct and r.content:
            return r.json()

        post_id = r.headers.get("x-restli-id") or r.headers.get("location")

        return {"status_code": r.status_code, "id": post_id, "note": "Created (no JSON body)."}
