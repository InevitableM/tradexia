"""FastAPI server — exposes ADK orchestrator over HTTP for the Node backend."""

from pathlib import Path
from dotenv import load_dotenv

# Load .env from ADK/ — must happen before any google.genai imports
load_dotenv(Path(__file__).parent / "ADK" / ".env")

import asyncio
import contextvars
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from google.genai import types
from loguru import logger

from ADK.agents.orchestrator import get_orchestrator, orchestrator_llm_agent
from ADK.core import get_main_runner
from ADK.tools.backend_client import get_backend_client


# ---------------------------------------------------------------------------
# Context var — holds the asyncio.Queue for the current streaming request.
# Orchestrator tools write status strings here; the SSE generator reads them.
# ---------------------------------------------------------------------------
_status_queue: contextvars.ContextVar[Optional[asyncio.Queue]] = contextvars.ContextVar(
    "_status_queue", default=None
)


async def emit_status(message: str) -> None:
    """Push a status update onto the current request's SSE queue (no-op if none)."""
    q = _status_queue.get()
    if q is not None:
        await q.put({"type": "status", "message": message})


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
# Shared logic — run the orchestrator and return the response text
# ---------------------------------------------------------------------------
async def _run_orchestrator(req: RunRequest) -> str:
    orchestrator = get_orchestrator()
    runner = orchestrator.runner

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

    return response_text


# ---------------------------------------------------------------------------
# POST /run  — plain JSON response (kept for backwards compat)
# ---------------------------------------------------------------------------
@app.post("/run", response_model=RunResponse)
async def run(req: RunRequest):
    logger.info(f"[/run] query={req.query!r} session_id={req.session_id} user_id={req.user_id}")
    try:
        response_text = await _run_orchestrator(req)

        if not response_text:
            raise HTTPException(status_code=502, detail="No response from orchestrator")

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
# POST /stream  — SSE: status events + final result
# ---------------------------------------------------------------------------
@app.post("/stream")
async def stream(req: RunRequest):
    logger.info(f"[/stream] query={req.query!r} session_id={req.session_id} user_id={req.user_id}")

    queue: asyncio.Queue = asyncio.Queue()

    async def generate() -> AsyncGenerator[str, None]:
        def _sse(payload: dict) -> str:
            return f"data: {json.dumps(payload)}\n\n"

        # Run the orchestrator in a background task so we can yield SSE
        # events from the queue while it executes.
        token = _status_queue.set(queue)
        try:
            task = asyncio.create_task(_run_orchestrator(req))

            # Drain the queue until the orchestrator task finishes
            while not task.done():
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield _sse(event)
                except asyncio.TimeoutError:
                    pass  # no new status yet — keep polling

            # Flush any remaining status events that arrived just before done
            while not queue.empty():
                yield _sse(queue.get_nowait())

            response_text = task.result()  # re-raises if the task threw

            if not response_text:
                yield _sse({"type": "error", "message": "No response from orchestrator"})
                return

            # Persist conversation
            await get_backend_client().save_conversation(
                session_id=req.session_id,
                user_message=req.query,
                assistant_message=response_text,
                access_token=req.access_token,
            )

            yield _sse({"type": "result", "message": response_text})
            yield _sse({"type": "done"})
            logger.info(f"[/stream] done session_id={req.session_id}")

        except Exception as e:
            logger.error(f"[/stream] error: {e}", exc_info=True)
            yield _sse({"type": "error", "message": str(e)})
        finally:
            _status_queue.reset(token)

    return StreamingResponse(generate(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
