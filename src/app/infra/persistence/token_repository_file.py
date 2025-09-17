import json

from pathlib import Path

from app.domain.models.token import Token
from app.domain.repository.token_repository import TokenRepository


class FileTokenRepository(TokenRepository):
    def __init__(self, path: str):
        self.path = Path(path)

        super().__init__()

    def load(self) -> Token:
        if not self.path.exists():
            return Token()

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))

            return Token(**data)
        except Exception:
            return Token()

    def save(self, token: Token) -> None:
        self.path.write_text(
            json.dumps(token.__dict__, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def get(self) -> Token:
        return self.load()

    def set(self, token: Token) -> None:
        self.save(token)
