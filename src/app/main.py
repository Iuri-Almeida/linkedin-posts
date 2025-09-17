from fastapi import FastAPI

from app.infra.routes import (
    auth,
    health,
    post
)

app = FastAPI(title="LinkedIn Poster API")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(post.router)
