from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
import json
from typing import Optional
from config.settings import get_settings
from llm.groq_client import GroqClient
from llm.schemas import ChatRequest, ChatResponse
from policy.engine import PolicyEngine

logger = logging.getLogger(__name__)

app = FastAPI(title="ControlPlane Gateway")
settings = get_settings()
groq_client = GroqClient(settings)
policy_engine = PolicyEngine()


class RequestState:
    session_id: str
    workflow: str
    start_time: datetime


@app.on_event("startup")
async def startup():
    logger.info(f"ControlPlane Gateway starting in {settings.controlplane_mode.upper()} mode")

    valid, msg = settings.validate_for_live_mode()
    if settings.is_live_mode and not valid:
        logger.warning(f"LIVE mode validation warning: {msg}")

    workflows = policy_engine.list_workflows()
    logger.info(f"Loaded {len(workflows)} workflows: {workflows}")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "mode": settings.controlplane_mode,
        "groq_configured": bool(settings.groq_api_key) if settings.is_live_mode else None,
    }


@app.get("/v1/controlplane/health")
async def controlplane_health():
    return {
        "status": "ok",
        "mode": settings.controlplane_mode,
        "groq_configured": bool(settings.groq_api_key) if settings.is_live_mode else None,
        "policy_loaded": len(policy_engine.list_workflows()) > 0,
        "embedding_loaded": False,
        "nli_loaded": False,
    }


@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatRequest,
    x_controlplane_workflow: Optional[str] = Header(None),
):
    try:
        workflow = x_controlplane_workflow or request.workflow or settings.default_workflow

        policy = policy_engine.get_policy(workflow)
        if not policy:
            raise HTTPException(status_code=400, detail=f"Workflow '{workflow}' not found")

        logger.info(f"Processing request for workflow: {workflow}")

        response, tokens_used, estimated_cost = groq_client.chat_completion(
            messages=request.messages,
            temperature=request.temperature or 0.7,
            tools=request.tools,
        )

        if not response:
            if settings.is_live_mode:
                raise HTTPException(
                    status_code=503,
                    detail="Groq service unavailable. Try DEMO or REPLAY mode.",
                )
            else:
                response = ChatResponse(
                    content="[DEMO MODE] This is a placeholder response.",
                    role="assistant",
                )
                tokens_used = {"input_tokens": 0, "output_tokens": 0}
                estimated_cost = 0.0

        return {
            "id": f"chatcmpl-{hash(str(request.messages))}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": settings.groq_model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": response.role,
                        "content": response.content,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": tokens_used.get("input_tokens", 0),
                "completion_tokens": tokens_used.get("output_tokens", 0),
                "total_tokens": sum(tokens_used.values()),
            },
            "metadata": {
                "workflow": workflow,
                "estimated_cost": estimated_cost,
                "mode": settings.controlplane_mode,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check logs for details."},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
