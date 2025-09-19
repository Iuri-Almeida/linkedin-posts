from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File
)

from app.application.services.post_service import PostService
from app.domain.models.post import Post
from app.domain.models.image_post import ImagePost
from app.utils.provider import get_post_service

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("")
async def posts(
    text: UploadFile = File(description="txt"),
    service: PostService = Depends(get_post_service)
):
    text_bytes = await text.read()

    return service.create_text_post(Post(text=text_bytes))


@router.post("/image")
async def post_image(
    text: UploadFile = File(description="txt"),
    file: UploadFile = File(description="jpg/png"),
    mime_type: str = "image/png",
    service: PostService = Depends(get_post_service)
):
    text_bytes = await text.read()
    file_bytes = await file.read()

    return service.create_image_post(ImagePost(text=text_bytes, file_bytes=file_bytes, mime_type=mime_type))
