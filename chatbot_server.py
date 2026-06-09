"""Small web chatbot for the Stage 5 A2A system.

Run Stage 5 first:
    OPENROUTER_MODEL=openai/gpt-4o-mini OPENROUTER_MAX_TOKENS=128 uv run ./start_all.sh

Then run this server:
    uv run python chatbot_server.py

Open:
    http://localhost:8080
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from uuid import uuid4

import httpx
import uvicorn
from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    TextPart,
)
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

load_dotenv()

APP_DIR = Path(__file__).resolve().parent
CUSTOMER_AGENT_URL = os.getenv("CUSTOMER_AGENT_URL", "http://localhost:10100")
LAW_AGENT_URL = os.getenv("LAW_AGENT_URL", "http://localhost:10101")

app = FastAPI(title="Stage 5 Chatbot Demo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3)
    target: str = Field(default="customer", pattern="^(customer|law)$")


def _part_text(part: object) -> str:
    inner = getattr(part, "root", part)
    return getattr(inner, "text", "") or ""


def extract_text(response: object) -> str:
    """Collect text from common A2A response shapes."""
    if hasattr(response, "root"):
        response = response.root

    result = getattr(response, "result", None)
    if result is None:
        return ""

    text = ""

    artifacts = getattr(result, "artifacts", None)
    if artifacts:
        for artifact in artifacts:
            for part in getattr(artifact, "parts", []) or []:
                text += _part_text(part)

    if not text:
        for part in getattr(result, "parts", []) or []:
            text += _part_text(part)

    if not text:
        status = getattr(result, "status", None)
        status_msg = getattr(status, "message", None)
        if status_msg is not None:
            for part in getattr(status_msg, "parts", []) or []:
                text += _part_text(part)

    if not text:
        for msg in getattr(result, "history", []) or []:
            for part in getattr(msg, "parts", []) or []:
                text += _part_text(part)

    return text


def extract_state(response: object) -> str:
    if hasattr(response, "root"):
        response = response.root
    result = getattr(response, "result", None)
    status = getattr(result, "status", None)
    state = getattr(status, "state", None)
    return getattr(state, "value", str(state or "unknown"))


async def send_a2a(endpoint: str, question: str) -> tuple[float, str, str]:
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=300.0) as http_client:
        card_resp = await http_client.get(f"{endpoint}/.well-known/agent.json")
        card_resp.raise_for_status()
        agent_card = AgentCard.model_validate(card_resp.json())
        client = A2AClient(httpx_client=http_client, agent_card=agent_card)

        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=question))],
            message_id=str(uuid4()),
        )
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(message=message),
        )
        response = await client.send_message(request)

    elapsed = time.perf_counter() - start
    return elapsed, extract_state(response), extract_text(response)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return (APP_DIR / "chatbot_demo.html").read_text(encoding="utf-8")


@app.get("/api/status")
async def status() -> dict:
    checks = {}
    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url in {
            "customer": CUSTOMER_AGENT_URL,
            "law": LAW_AGENT_URL,
        }.items():
            try:
                resp = await client.get(f"{url}/.well-known/agent.json")
                checks[name] = {"ok": resp.status_code == 200, "url": url}
            except Exception as exc:
                checks[name] = {"ok": False, "url": url, "error": str(exc)}
    return checks


@app.post("/api/chat")
async def chat(req: ChatRequest) -> dict:
    endpoint = CUSTOMER_AGENT_URL if req.target == "customer" else LAW_AGENT_URL
    try:
        latency, state, answer = await send_a2a(endpoint, req.question)
        return {
            "ok": state == "completed" and bool(answer),
            "target": req.target,
            "latency": round(latency, 2),
            "state": state,
            "answer": answer or "No text response received.",
        }
    except Exception as exc:
        return {
            "ok": False,
            "target": req.target,
            "latency": None,
            "state": "error",
            "answer": f"Request failed: {exc}",
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("CHATBOT_PORT", "8080")))
