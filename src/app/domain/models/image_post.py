from typing import Literal

from app.domain.models.post import Post


class ImagePost(Post):
    file_bytes: bytes
    mime_type: Literal["image/jpeg", "image/png"]
