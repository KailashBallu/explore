from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.meetings import router as meetings_router

app = FastAPI(title="Meeting Intelligence")

app.include_router(auth_router)
app.include_router(meetings_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
