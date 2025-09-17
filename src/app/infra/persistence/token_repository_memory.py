from app.domain.models.token import Token
from app.domain.repository.token_repository import TokenRepository


class MemoryTokenRepository(TokenRepository):
    def __init__(self):
        self.__token = Token()

        super().__init__()

    def load(self) -> Token:
        return self.__token

    def save(self, token: Token) -> None:
        self.__token = token

    def get(self) -> Token:
        return self.__token

    def set(self, token: Token) -> None:
        self.__token = token
