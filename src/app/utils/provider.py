from functools import lru_cache

from app.config.settings import Settings
from app.domain.repository.token_repository import TokenRepository
from app.infra.persistence.token_repository_memory import MemoryTokenRepository
from app.infra.client.linkedin_client import LinkedInClient


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


@lru_cache(maxsize=1)
def get_repository() -> TokenRepository:
    return MemoryTokenRepository()


@lru_cache(maxsize=1)
def get_client() -> LinkedInClient:
    return LinkedInClient(get_settings(), get_repository())
