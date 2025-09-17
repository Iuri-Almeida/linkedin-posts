from fastapi import HTTPException

from app.domain.models.post import Post
from app.infra.client.linkedin_client import LinkedInClient


class PostService:
    def __init__(self, client: LinkedInClient):
        self.__client = client

    def create_post(self, post: Post):
        resp = self.__client.create_text_post(post)

        if isinstance(resp, dict) and resp.get("error"):
            raise HTTPException(status_code=resp.get("status_code", 400), detail=resp)

        return resp
