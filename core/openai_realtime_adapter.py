"""OpenAI Realtime adapter for JARVIS.

Presents the small Gemini-Live-shaped interface main.py already uses so
JARVIS memory, tools, plugins, desktop audio, and phone audio stay shared.
"""
from __future__ import annotations

import audioop
import base64
import json
from types import SimpleNamespace as NS
from typing import Any

import websockets


def _ns_response(*, data=None, server_content=None, tool_call=None):
    return NS(data=data, server_content=server_content, tool_call=tool_call)


def normalize_schema(value: Any) -> Any:
    """Convert Gemini-style JSON schema type names to OpenAI JSON Schema."""
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if key == "type" and isinstance(item, str):
                out[key] = item.lower()
            else:
                out[key] = normalize_schema(item)
        return out
    if isinstance(value, list):
        return [normalize_schema(v) for v in value]
    return value


def build_openai_tools(declarations: list[dict]) -> list[dict]:
    tools = []
    for decl in declarations:
        item = {
            "type": "function",
            "name": decl["name"],
            "description": decl.get("description", ""),
            "parameters": normalize_schema(decl.get("parameters", {"type": "OBJECT"})),
        }
        tools.append(item)
    return tools


class OpenAIRealtimeSession:
    """Async context manager + session API compatible with JARVIS main loop."""

    def __init__(self, api_key: str, model: str, config: dict):
        self.api_key = api_key.strip()
        self.model = model
        self.config = dict(config)
        self.ws = None
        self._rate_state = None

    async def __aenter__(self):
        url = f"wss://api.openai.com/v1/realtime?model={self.model}"
        self.ws = await websockets.connect(
            url,
            additional_headers={"Authorization": f"Bearer {self.api_key}"},
            max_size=None,
            ping_interval=20,
            ping_timeout=20,
        )
        first = json.loads(await self.ws.recv())
        if first.get("type") == "error":
            raise RuntimeError(self._error_text(first))
        await self._send({"type": "session.update", "session": self.config})

        while True:
            event = json.loads(await self.ws.recv())
            etype = event.get("type")
            if etype == "session.updated":
                break
            if etype == "error":
                raise RuntimeError(self._error_text(event))
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.ws is not None:
            try:
                await self.ws.close()
            except Exception:
                pass
        self.ws = None
        return False

    @staticmethod
    def _error_text(event: dict) -> str:
        err = event.get("error") or {}
        if isinstance(err, dict):
            return f"OpenAI Realtime error: {err.get('code') or ''} {err.get('message') or err}"
        return f"OpenAI Realtime error: {err}"

    async def _send(self, event: dict) -> None:
        if self.ws is None:
            raise RuntimeError("OpenAI Realtime session is not connected")
        await self.ws.send(json.dumps(event, separators=(",", ":"), default=str))

    async def send_realtime_input(self, media: dict) -> None:
        data = media.get("data") or b""
        if not data:
            return
        mime = str(media.get("mime_type") or "")
        if "rate=16000" in mime:
            data, self._rate_state = audioop.ratecv(
                data, 2, 1, 16000, 24000, self._rate_state
            )
        await self._send({
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(data).decode("ascii"),
        })

    async def send_client_content(self, turns: dict, turn_complete: bool = True) -> None:
        parts = turns.get("parts", []) if isinstance(turns, dict) else []
        content = []
        for part in parts:
            if not isinstance(part, dict):
                continue
            if part.get("text") is not None:
                content.append({"type": "input_text", "text": str(part["text"])})
                continue
            inline = part.get("inline_data") or {}
            if inline:
                mime = inline.get("mime_type") or "image/png"
                raw = inline.get("data") or ""
                if isinstance(raw, bytes):
                    raw = base64.b64encode(raw).decode("ascii")
                content.append({"type": "input_image", "image_url": f"data:{mime};base64,{raw}"})
        if content:
            await self._send({
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": content,
                },
            })
        if turn_complete:
            await self._send({"type": "response.create"})

    async def send_tool_response(self, function_responses: list) -> None:
        for response in function_responses:
            call_id = getattr(response, "id", "")
            payload = getattr(response, "response", {})
            if hasattr(payload, "model_dump"):
                payload = payload.model_dump()
            await self._send({
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(payload, ensure_ascii=False, default=str),
                },
            })
        await self._send({"type": "response.create"})

    async def cancel_response(self) -> None:
        try:
            await self._send({"type": "response.cancel"})
        except Exception:
            pass

    async def receive(self):
        if self.ws is None:
            return
        while True:
            raw = await self.ws.recv()
            event = json.loads(raw)
            etype = event.get("type", "")

            if etype == "error":
                raise RuntimeError(self._error_text(event))

            if etype == "response.output_audio.delta":
                data = base64.b64decode(event.get("delta") or "")
                if data:
                    yield _ns_response(data=data)
                continue

            if etype == "conversation.item.input_audio_transcription.completed":
                text = str(event.get("transcript") or "").strip()
                if text:
                    sc = NS(
                        input_transcription=NS(text=text),
                        output_transcription=None,
                        turn_complete=False,
                    )
                    yield _ns_response(server_content=sc)
                continue
            if etype == "response.output_audio_transcript.done":
                text = str(event.get("transcript") or "").strip()
                if text:
                    sc = NS(
                        input_transcription=None,
                        output_transcription=NS(text=text),
                        turn_complete=False,
                    )
                    yield _ns_response(server_content=sc)
                continue

            if etype == "response.function_call_arguments.done":
                try:
                    args = json.loads(event.get("arguments") or "{}")
                except Exception:
                    args = {}
                fc = NS(
                    id=str(event.get("call_id") or event.get("item_id") or ""),
                    name=str(event.get("name") or ""),
                    args=args,
                )
                yield _ns_response(tool_call=NS(function_calls=[fc]))
                continue

            if etype == "response.done":
                sc = NS(
                    input_transcription=None,
                    output_transcription=None,
                    turn_complete=True,
                )
                yield _ns_response(server_content=sc)
