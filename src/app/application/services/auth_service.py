from fastapi import HTTPException

from app.domain.models.token import Token
from app.infra.client.linkedin_client import LinkedInClient


class AuthService:
    def __init__(self, client: LinkedInClient):
        self.__client = client

    def authorize_url(self) -> str:
        return self.__client.build_authorize_url()

    def handle_callback(self, code: str) -> dict:
        try:
            token_bundle: Token = self.__client.exchange_code(code)

            return {"message": "LinkedIn connected", "author": token_bundle.person_urn}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def status(self) -> dict:
        token_bundle = self.__client.refresh_if_needed() if self.__client.repository.get().access_token else self.__client.repository.get()

        return {
            "logged_in": bool(token_bundle.access_token),
            "has_refresh": bool(token_bundle.refresh_token),
            "expires_at": token_bundle.expires_at,
            "author": token_bundle.person_urn,
        }
