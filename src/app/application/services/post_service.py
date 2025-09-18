from fastapi import HTTPException

from app.domain.models.post import Post
from app.domain.models.image_post import ImagePost
from app.infra.client.linkedin_client import LinkedInClient


class PostService:
    def __init__(self, client: LinkedInClient):
        self.__client = client

    def create_text_post(self, post: Post):
        resp = self.__client.create_post(post)

        if isinstance(resp, dict) and resp.get("error"):
            raise HTTPException(status_code=resp.get("status_code", 400), detail=resp)

        return resp

    def create_image_post(self, image_post: ImagePost):
        resp = self.__client.process_image(image_post)

        if isinstance(resp, dict) and resp.get("error"):
            raise HTTPException(status_code=resp.get("status_code", 400), detail=resp)

        return resp
