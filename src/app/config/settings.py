from pathlib import Path
from typing import Annotated
from datetime import datetime
from pydantic import StringConstraints
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)

ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT / ".env"


class Settings(BaseSettings):
    LI_CLIENT_ID    : Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    LI_CLIENT_SECRET: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    LI_REDIRECT_URI : str = "http://localhost:8000/auth/callback"
    LI_SCOPES       : str = "openid profile email w_member_social"

    LINKEDIN_VERSION: str = datetime.now().strftime("%Y%m")

    SERVICE_NAME    : str = "linkedin-poster-api"

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
    )


