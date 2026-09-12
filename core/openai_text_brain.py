"""Text-only OpenAI Responses API helper for JARVIS.

Voice transport is intentionally kept outside OpenAI: local Whisper handles
speech-to-text and Gemini Live/Charon handles text-to-speech.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

TEXT_MODEL = (os.getenv("OPENAI_TEXT_MODEL") or "gpt-5.6-sol").strip()
TEXT_REASONING_EFFORT = (os.getenv("OPENAI_TEXT_REASONING_EFFORT") or "medium").strip()
TEXT_TIMEOUT_SECONDS = int(os.getenv("OPENAI_TEXT_TIMEOUT_SECONDS") or "90")


def _lower_schema(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if key == "type" and isinstance(item, str):
                out[key] = item.lower()
            else:
                out[key] = _lower_schema(item)
        return out
    if isinstance(value, list):
        return [_lower_schema(item) for item in value]
    return value


def build_response_tools(declarations: list[dict]) -> list[dict]:
    tools: list[dict] = []
    for decl in declarations:
        name = str(decl.get("name") or "").strip()
        if not name:
            continue
        tools.append({
            "type": "function",
            "name": name,
            "description": str(decl.get("description") or "")[:4096],
            "parameters": _lower_schema(decl.get("parameters") or {"type": "object", "properties": {}}),
        })
    return tools


def _extract_error(exc: urllib.error.HTTPError) -> str:
    try:
        payload = json.loads(exc.read().decode("utf-8"))
        err = payload.get("error") or {}
        code = str(err.get("code") or "")
        msg = str(err.get("message") or "")
        return " ".join(part for part in (code, msg) if part).strip()
    except Exception:
        return ""


def _post(api_key: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TEXT_TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = _extract_error(exc)
        raise RuntimeError(f"OpenAI text brain HTTP {exc.code}: {detail[:300]}") from exc
    except Exception as exc:
        raise RuntimeError(f"OpenAI text brain request failed: {exc}") from exc


def create_response(
    api_key: str,
    *,
    instructions: str,
    user_text: str = "",
    tools: list[dict] | None = None,
    previous_response_id: str = "",
    tool_outputs: list[dict] | None = None,
) -> dict:
    key = (api_key or "").strip()
    if not key:
        raise RuntimeError("OpenAI API key unavailable for text brain")
    payload: dict[str, Any] = {
        "model": TEXT_MODEL,
        "instructions": instructions,
        "reasoning": {"effort": TEXT_REASONING_EFFORT},
        "text": {"verbosity": "low"},
        "max_output_tokens": 4096,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    if previous_response_id:
        payload["previous_response_id"] = previous_response_id
    if tool_outputs:
        payload["input"] = tool_outputs
    else:
        payload["input"] = user_text
    return _post(key, payload)


def extract_output_text(payload: dict) -> str:
    direct = str(payload.get("output_text") or "").strip()
    if direct:
        return direct
    chunks: list[str] = []
    for item in payload.get("output") or []:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            if not isinstance(content, dict):
                continue
            if content.get("type") in {"output_text", "text"}:
                text = str(content.get("text") or "").strip()
                if text:
                    chunks.append(text)
    return "\n".join(chunks).strip()


def extract_function_calls(payload: dict) -> list[dict]:
    calls: list[dict] = []
    for item in payload.get("output") or []:
        if not isinstance(item, dict) or item.get("type") != "function_call":
            continue
        calls.append({
            "call_id": str(item.get("call_id") or item.get("id") or ""),
            "name": str(item.get("name") or ""),
            "arguments": str(item.get("arguments") or "{}"),
        })
    return calls
