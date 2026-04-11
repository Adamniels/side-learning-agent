from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, ConfigDict, Field

from session_designer.domain.models import UserLearningContext
from session_designer.graph.builder import run_session_design
from session_designer.graph.deps import GraphDeps
from session_designer.providers.anthropic_provider import AnthropicLLMProvider
from session_designer.providers.mock_provider import MockLLMProvider
from session_designer.resources.gatherer import LLMResourceGatherer

# Load .env from package project root (create-session-agent/.env), then cwd — Python does not read .env by itself.
_project_root = Path(__file__).resolve().parents[2]
load_dotenv(_project_root / ".env")
load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="Session designer service", version="0.1.0")

SECRET_HEADER = "X-Session-Designer-Secret"
_CALLBACK_DELAYS_SEC = (1, 2, 4, 8, 16)
_MAX_CALLBACK_ATTEMPTS = 5


class DesignJobRequest(BaseModel):
    """Inbound body from .NET (camelCase)."""

    model_config = ConfigDict(populate_by_name=True)

    job_id: UUID = Field(alias="jobId")
    callback_url: str = Field(alias="callbackUrl")
    user_learning_context: UserLearningContext = Field(alias="userLearningContext")


class DesignJobAcceptedResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    job_id: UUID = Field(serialization_alias="jobId")
    status: str = "accepted"


def _build_graph_deps() -> GraphDeps:
    use_mock = os.environ.get("SESSION_DESIGNER_USE_MOCK", "").lower() in ("1", "true", "yes")
    if use_mock:
        llm: MockLLMProvider | AnthropicLLMProvider = MockLLMProvider()
        model = "mock"
    else:
        llm = AnthropicLLMProvider()
        model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    max_revisions = int(os.environ.get("SESSION_DESIGNER_MAX_REVISIONS", "2"))
    gatherer = LLMResourceGatherer(llm)
    return GraphDeps(llm=llm, resource_gatherer=gatherer, model=model, max_revisions=max_revisions)


def _callback_secret() -> str:
    return os.environ.get("SESSION_DESIGNER_SHARED_SECRET", "").strip()


async def _post_callback_with_retries(callback_url: str, body: dict[str, Any]) -> None:
    secret = _callback_secret()
    headers = {SECRET_HEADER: secret} if secret else {}

    for attempt in range(_MAX_CALLBACK_ATTEMPTS):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
                response = await client.post(callback_url, json=body, headers=headers)
        except httpx.RequestError as exc:
            logger.warning(
                "Callback request error for %s (attempt %s/%s): %s",
                callback_url,
                attempt + 1,
                _MAX_CALLBACK_ATTEMPTS,
                exc,
            )
            if attempt < _MAX_CALLBACK_ATTEMPTS - 1:
                await asyncio.sleep(_CALLBACK_DELAYS_SEC[attempt])
            continue

        if response.status_code == 401:
            logger.error("Callback rejected with 401 for %s — not retrying.", callback_url)
            return
        if response.status_code == 400:
            logger.error(
                "Callback rejected with 400 for %s: %s — not retrying.",
                callback_url,
                response.text[:500],
            )
            return
        if 500 <= response.status_code < 600:
            logger.warning(
                "Callback server error %s for %s (attempt %s/%s)",
                response.status_code,
                callback_url,
                attempt + 1,
                _MAX_CALLBACK_ATTEMPTS,
            )
            if attempt < _MAX_CALLBACK_ATTEMPTS - 1:
                await asyncio.sleep(_CALLBACK_DELAYS_SEC[attempt])
            continue

        if response.is_success:
            logger.info("Callback succeeded for job callback %s", callback_url)
            return

        logger.warning(
            "Unexpected callback status %s for %s: %s",
            response.status_code,
            callback_url,
            response.text[:500],
        )
        return

    logger.error("Callback failed after %s attempts for %s", _MAX_CALLBACK_ATTEMPTS, callback_url)


async def _run_design_and_callback(req: DesignJobRequest) -> None:
    deps = _build_graph_deps()
    try:
        result = await asyncio.to_thread(run_session_design, deps, req.user_learning_context)
        body: dict[str, Any] = {
            "outcome": "succeeded",
            "sessionDesignResult": result.model_dump(mode="json"),
        }
    except Exception:
        logger.exception("Session design graph failed for job %s", req.job_id)
        body = {
            "outcome": "failed",
            "error": {
                "code": "design_error",
                "message": "Session design failed.",
            },
        }

    await _post_callback_with_retries(req.callback_url, body)


@app.post("/v1/design-jobs", status_code=202, response_model=DesignJobAcceptedResponse)
async def accept_design_job(
    req: DesignJobRequest,
    background_tasks: BackgroundTasks,
) -> DesignJobAcceptedResponse:
    """Return 202 immediately; run LangGraph and POST results to callback_url."""
    background_tasks.add_task(_run_design_and_callback, req)
    return DesignJobAcceptedResponse(job_id=req.job_id, status="accepted")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
