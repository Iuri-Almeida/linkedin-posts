from functools import lru_cache

from app.application.services.auth_service import AuthService
from app.application.services.health_service import HealthService
from app.application.services.post_service import PostService
from app.config.settings import Settings
from app.domain.repository.token_repository import TokenRepository
from app.infra.client.linkedin_client import LinkedInClient
from app.infra.persistence.token_repository_file import FileTokenRepository
from app.infra.persistence.token_repository_memory import MemoryTokenRepository


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


@lru_cache(maxsize=1)
def get_repository() -> TokenRepository:
    settings = get_settings()

    # return MemoryTokenRepository()
    return FileTokenRepository(settings.TOKENS_PATH)


@lru_cache(maxsize=1)
def get_client() -> LinkedInClient:
    return LinkedInClient(get_settings(), get_repository())


def get_health_service() -> HealthService:
    return HealthService(get_settings())


def get_auth_service() -> AuthService:
    return AuthService(get_client())


def get_post_service() -> PostService:
    return PostService(get_client())
