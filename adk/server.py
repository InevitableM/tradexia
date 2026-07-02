"""FastAPI server — exposes ADK orchestrator over HTTP for the Node backend."""

from pathlib import Path
from dotenv import load_dotenv

# Load .env from ADK/ — must happen before any google.genai imports
load_dotenv(Path(__file__).parent / "ADK" / ".env")

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.genai import types
from loguru import logger

from ADK.agents.orchestrator import get_orchestrator, orchestrator_llm_agent
from ADK.core import get_main_runner
from ADK.tools.backend_client import get_backend_client


# ---------------------------------------------------------------------------
# Lifespan — warm up the orchestrator once at startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ADK server — warming up orchestrator...")
    get_orchestrator()
    logger.info("Orchestrator ready")
    yield
    logger.info("ADK server shutting down")


app = FastAPI(title="Tradexia ADK", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class RunRequest(BaseModel):
    query: str
    session_id: str
    user_id: str
    access_token: str


class RunResponse(BaseModel):
    response: str
    session_id: str
    user_id: str


# ---------------------------------------------------------------------------
# POST /run  — called by Node backend
# ---------------------------------------------------------------------------
@app.post("/run", response_model=RunResponse)
async def run(req: RunRequest):
    logger.info(f"[/run] query={req.query!r} session_id={req.session_id} user_id={req.user_id}")
    try:
        orchestrator = get_orchestrator()
        runner = orchestrator.runner

        # Get or create ADK session
        session = await runner.session_service.get_session(
            app_name=runner.app_name,
            user_id=req.user_id,
            session_id=req.session_id,
        )
        if not session:
            session = await runner.session_service.create_session(
                app_name=runner.app_name,
                user_id=req.user_id,
                session_id=req.session_id,
            )

        content = types.Content(role="user", parts=[types.Part(text=req.query)])

        response_text = ""
        async for event in runner.run_async(
            session_id=session.id,
            user_id=req.user_id,
            new_message=content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                response_text = "".join(
                    part.text for part in event.content.parts if hasattr(part, "text") and part.text
                )

        if not response_text:
            raise HTTPException(status_code=502, detail="No response from orchestrator")

        # Persist both messages to the Node backend
        await get_backend_client().save_conversation(
            session_id=req.session_id,
            user_message=req.query,
            assistant_message=response_text,
            access_token=req.access_token,
        )

        logger.info(f"[/run] done session_id={req.session_id}")
        return RunResponse(response=response_text, session_id=req.session_id, user_id=req.user_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[/run] error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
