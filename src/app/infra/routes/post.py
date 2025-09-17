from fastapi import (
    APIRouter,
    Depends
)

from app.application.services.post_service import PostService
from app.domain.models.post import Post
from app.utils.provider import get_post_service

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("")
def posts(post: Post, service: PostService = Depends(get_post_service)):
    return service.create_post(post)
