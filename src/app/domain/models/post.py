from typing import Annotated
from pydantic import (
    BaseModel,
    StringConstraints
)


class Post(BaseModel):
    text      : Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    visibility: str = "PUBLIC"
    hashtags  : str = ""
