"""FastAPI app entrypoint for the Tradexia RAG service."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

from db import db
from routes import ingest, retrieve


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[server] starting up")
    try:
        await db.connect()
    except Exception:
        logger.exception("[server] failed to connect to database")
        raise
    logger.info("[server] startup complete")
    yield
    logger.info("[server] shutting down")
    await db.disconnect()
    logger.info("[server] shutdown complete")


app = FastAPI(title="Tradexia RAG Service", lifespan=lifespan)
app.include_router(ingest.router)
app.include_router(retrieve.router)

# Log every registered route at import time, so a missing/misregistered
# endpoint is visible immediately instead of surfacing as a silent 404.
for route in app.routes:
    methods = getattr(route, "methods", None)
    path = getattr(route, "path", None)
    if methods and path:
        logger.info(f"[server] route registered: {sorted(methods)} {path}")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
