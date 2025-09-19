from pydantic import (
    BaseModel,
    field_validator,
    StringConstraints
)
from typing import (
    Annotated,
    Any
)


class Post(BaseModel):
    text      : Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2950)]
    visibility: str = "PUBLIC"
    hashtags  : str = ""

    @field_validator("text", mode="before")
    @classmethod
    def bytes_to_formatted_string(cls, v: Any) -> str:
        if isinstance(v, (bytes, bytearray, memoryview)):
            try:
                return bytes(v).decode(encoding="utf-8").replace("(", "\(").replace(")", "\)")
            except UnicodeDecodeError:
                return bytes(v).decode(encoding="utf-8", errors="replace").replace("(", "\(").replace(")", "\)")

        if isinstance(v, str):
            return v

        raise TypeError("Field 'text' must be str or bytes!")
