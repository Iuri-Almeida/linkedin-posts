from datetime import datetime
from pathlib import Path
from pydantic import StringConstraints
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)
from typing import Annotated

ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT / ".env"
TOKENS_PATH = ROOT / ".tokens.json"
IMAGE_PATH = ROOT / "image.png"


class Settings(BaseSettings):
    LI_CLIENT_ID    : Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    LI_CLIENT_SECRET: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

    LI_REDIRECT_URI : str = "http://localhost:8000/auth/callback"
    LI_SCOPES       : str = "openid profile email w_member_social"

    LINKEDIN_VERSION: str = datetime.now().strftime("%Y%m")

    SERVICE_NAME    : str = "linkedin-poster-api"

    LI_AUTH_URL : str = "https://www.linkedin.com/oauth/v2/authorization"
    LI_TOKEN_URL: str = "https://www.linkedin.com/oauth/v2/accessToken"
    LI_POSTS_URL: str = "https://api.linkedin.com/rest/posts"

    LI_REGISTER_UPLOAD_URL: str = "https://api.linkedin.com/rest/images?action=initializeUpload"

    TOKENS_PATH: str = str(TOKENS_PATH)

    IMAGE_PATH: str = str(IMAGE_PATH)

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
    )
