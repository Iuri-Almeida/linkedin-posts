from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="LinkedIn Poster API")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "linkedin-poster-api",
        "ts": datetime.now()
    }
