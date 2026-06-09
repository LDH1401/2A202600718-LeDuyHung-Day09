"""Measure Stage 5 A2A latency.

Baseline target:
    customer -> Customer Agent -> Law Agent -> Tax/Compliance -> Customer

Optimized target:
    law -> Law Agent -> Tax/Compliance

The optimized path is useful when the caller already knows the question is a
legal question, so it can skip the Customer Agent's classification/delegation
LLM step.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import statistics
import time
from uuid import uuid4

import httpx
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


QUESTION = (
    "If a company breaks a contract and avoids taxes, "
    "what are the legal and regulatory consequences?"
)

TARGETS = {
    "customer": (
        "Full Stage 5 via Customer Agent",
        "CUSTOMER_AGENT_URL",
        "http://localhost:10100",
    ),
    "law": (
        "Optimized direct Law Agent path",
        "LAW_AGENT_URL",
        "http://localhost:10101",
    ),
}


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


async def send_once(endpoint: str, question: str) -> tuple[float, str, str]:
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


async def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Measure Stage 5 A2A latency.")
    parser.add_argument(
        "--target",
        choices=sorted(TARGETS),
        default="customer",
        help="customer = full Stage 5, law = optimized direct Law Agent path",
    )
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--question", default=QUESTION)
    args = parser.parse_args()

    label, env_name, default_url = TARGETS[args.target]
    endpoint = os.getenv(env_name, default_url)

    print(f"Target: {args.target} ({label})")
    print(f"Endpoint: {endpoint}")
    print(f"Question: {args.question}")
    print("-" * 70)

    latencies: list[float] = []
    last_text = ""
    last_state = "unknown"

    for idx in range(1, args.runs + 1):
        elapsed, state, text = await send_once(endpoint, args.question)
        latencies.append(elapsed)
        last_text = text
        last_state = state
        print(
            f"Run {idx}: latency={elapsed:.2f}s "
            f"state={state} response_chars={len(text)}"
        )

    print("-" * 70)
    print(f"Average latency: {statistics.mean(latencies):.2f}s")
    if len(latencies) > 1:
        print(f"Median latency: {statistics.median(latencies):.2f}s")
    print(f"Last state: {last_state}")
    print("Response preview:")
    print((last_text or "<no text response>").strip()[:1000])


if __name__ == "__main__":
    asyncio.run(main())
