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
def posts(post: Post, service: PostService = Depends(get_post_service)):
    return service.create_text_post(post)


@router.post("/image")
async def post_image(
    text: str = "Test text",
    file: UploadFile = File(description="jpg/png"),
    mime_type: str = "image/png",
    service: PostService = Depends(get_post_service)
):
    data = await file.read()

    return service.create_image_post(ImagePost(text=text, file_bytes=data, mime_type=mime_type))
