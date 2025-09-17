from datetime import (
    datetime,
    timezone
)

from app.config.settings import Settings


class HealthService:
    def __init__(self, settings: Settings):
        self.__settings = settings

    def get_health(self) -> dict[str, str]:
        return {
            "status": "ok",
            "service": self.__settings.SERVICE_NAME,
            "ts_utc": datetime\
                        .now(timezone.utc)
                        .isoformat(timespec="seconds")
                        .replace("+00:00","Z")
        }

    def get_env_check(self):
        return {
            "client_id_set": bool(self.__settings.LI_CLIENT_ID),
            "redirect_uri": self.__settings.LI_REDIRECT_URI
        }
