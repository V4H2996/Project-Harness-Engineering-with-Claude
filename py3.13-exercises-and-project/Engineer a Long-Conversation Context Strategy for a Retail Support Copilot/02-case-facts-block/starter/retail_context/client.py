"""Anthropic client + model configuration.

Two inference paths are supported:

1. **SDK path (preferred / exemplar)** — used when `ANTHROPIC_API_KEY` is set.
   Direct Anthropic Python SDK calls. This is what you use in the Docker
   container with the project's $25 API credit.

2. **Claude Code CLI path (fallback)** — used when no API key is set but the
   `claude` CLI is available and authenticated. Shells out to
   `claude -p --output-format json --model <model>`. This is purely a
   convenience for local development against an existing Claude Code session
   subscription — it does not represent the canonical workflow.

`CLAUDE_MODEL` env var overrides the default model in either path.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from functools import lru_cache
from typing import Any, Literal

import anthropic
import httpx

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
InferenceBackend = Literal["sdk", "cli"]


@lru_cache(maxsize=1)
def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def get_model() -> str:
    """`CLAUDE_MODEL` if set, else the lab's `ANTHROPIC_MODEL`, else DEFAULT_MODEL."""
    return os.environ.get("CLAUDE_MODEL") or os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL


def set_model(model: str) -> None:
    os.environ["CLAUDE_MODEL"] = model


def _backend() -> InferenceBackend:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "sdk"
    if shutil.which("claude"):
        return "cli"
    raise RuntimeError(
        "No inference backend available. Set ANTHROPIC_API_KEY or install the `claude` CLI."
    )


def _lenient_json_loads(raw: str) -> Any:
    """Parse JSON, tolerating trailing "extra data" after the first JSON object.

    The claude.vocareum.com proxy appends bytes after the JSON body, which makes
    stdlib json.loads() raise JSONDecodeError("Extra data"). raw_decode extracts
    just the first valid JSON object and ignores the rest.
    """
    raw = raw.strip()
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(raw)
    return obj


def complete(prompt: str, *, model: str | None = None, max_tokens: int = 2048) -> str:
    """Issue a single user-turn completion and return the assistant's text."""
    target_model = model or get_model()
    backend = _backend()
    if backend == "sdk":
        resp = get_client().messages.create(
            model=target_model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip()

    # CLI fallback
    result = subprocess.run(
        ["claude", "-p", "--model", target_model, "--output-format", "json", prompt],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    return (payload.get("result") or "").strip()


def complete_with_system(
    system: str,
    user: str,
    *,
    model: str | None = None,
    max_tokens: int = 2048,
) -> tuple[str, int, int]:
    """Issue a system + user-turn call. Returns (text, input_tokens, output_tokens)."""
    target_model = model or get_model()
    backend = _backend()
    if backend == "sdk":
        # Use raw httpx with lenient JSON parsing. The anthropic SDK calls
        # response.json() strictly, which fails on the lab proxy that returns
        # "Extra data" after the JSON body.
        base_url = os.environ.get(
            "ANTHROPIC_BASE_URL", "https://api.anthropic.com"
        ).rstrip("/")
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": target_model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        resp = httpx.post(
            f"{base_url}/v1/messages",
            headers=headers,
            json=body,
            timeout=60.0,
        )
        resp.raise_for_status()
        payload = _lenient_json_loads(resp.text)
        text = "".join(
            b.get("text", "")
            for b in payload.get("content", [])
            if b.get("type") == "text"
        ).strip()
        usage = payload.get("usage", {})
        return text, int(usage.get("input_tokens", 0)), int(usage.get("output_tokens", 0))

    # CLI fallback
    result = subprocess.run(
        ["claude", "-p", "--model", target_model, "--output-format", "json", user],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    return (payload.get("result") or "").strip()