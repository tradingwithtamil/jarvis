"""Jarvis -> LeadFlow AI Workforce delegation bridge."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid

PLUGIN = {
    "name": "leadflow_delegate",
    "description": (
        "Delegate SAFE read/analysis work to LeadFlow AI Workspace agents and read the result. "
        "Use this when BOSS asks to give/assign/delegate work to a LeadFlow agent, department, "
        "AI CEO, Sales agent, Support agent, Finance agent, etc. delegate_ai_work executes only "
        "server-enforced read-only tools; CRM/customer mutations are not permitted through this bridge."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "delegate_ai_work, get_ai_work_status, or list_ai_work"},
            "arguments": {
                "type": "OBJECT",
                "properties": {
                    "task": {"type": "STRING", "description": "Work instruction for the LeadFlow AI agent."},
                    "title": {"type": "STRING"},
                    "agentId": {"type": "STRING"},
                    "agentName": {"type": "STRING"},
                    "role": {"type": "STRING"},
                    "department": {"type": "STRING"},
                    "priority": {"type": "STRING"},
                    "workId": {"type": "STRING"},
                    "status": {"type": "STRING"},
                    "limit": {"type": "NUMBER"},
                    "context": {"type": "OBJECT", "properties": {}},
                },
            },
        },
        "required": ["action"],
    },
}

_ALIASES = {
    "delegate": "delegate_ai_work",
    "delegate_work": "delegate_ai_work",
    "assign_ai_work": "delegate_ai_work",
    "assign_work": "delegate_ai_work",
    "give_work_to_agent": "delegate_ai_work",
    "agent_work": "delegate_ai_work",
    "work_status": "get_ai_work_status",
    "agent_work_status": "get_ai_work_status",
    "recent_ai_work": "list_ai_work",
}
_ALLOWED = {"delegate_ai_work", "get_ai_work_status", "list_ai_work"}


def _endpoint() -> str:
    explicit = os.getenv("LEADFLOW_DELEGATION_MCP_URL", "").strip()
    if explicit:
        return explicit
    base = os.getenv("LEADFLOW_MCP_URL", "").strip()
    if "/api/mcp/leadflow" in base:
        return base.split("/api/mcp/leadflow", 1)[0] + "/api/mcp/jarvis-delegation"
    return "https://leadflow.forextamil.com/api/mcp/jarvis-delegation"


def _token(action: str) -> str:
    if action == "delegate_ai_work":
        token = os.getenv("LEADFLOW_MCP_ADMIN_TOKEN", "").strip()
        if not token:
            raise RuntimeError("LeadFlow admin MCP token is not configured in JARVIS Keychain.")
        return token
    token = os.getenv("LEADFLOW_MCP_TOKEN", "").strip() or os.getenv("LEADFLOW_MCP_ADMIN_TOKEN", "").strip()
    if not token:
        raise RuntimeError("LeadFlow MCP token is not configured in JARVIS Keychain.")
    return token


def _call(action: str, arguments: dict):
    url = _endpoint()
    if not url.startswith("https://"):
        raise RuntimeError("LeadFlow delegation MCP endpoint must use HTTPS.")
    body = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",
        "params": {"name": action, "arguments": arguments},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {_token(action)}",
            "User-Agent": "DarkFlow-Jarvis/LeadFlow-Delegation",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            payload = json.loads(response.read(2_000_000).decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read(4096).decode("utf-8", errors="replace")
        raise RuntimeError(f"LeadFlow delegation HTTP {exc.code}: {detail[:700]}") from exc
    if payload.get("error"):
        raise RuntimeError(str((payload.get("error") or {}).get("message") or "LeadFlow delegation error"))
    result = payload.get("result") or {}
    return result.get("structuredContent", result)


def _format(value) -> str:
    if value is None:
        return "BOSS, matching delegated AI work record கிடைக்கல."
    if isinstance(value, list):
        if not value:
            return "BOSS, delegated AI work history empty-aa இருக்கு."
        parts = []
        for row in value[:20]:
            if isinstance(row, dict):
                parts.append(f"{row.get('id','')} · {row.get('agent_name','AI agent')} · {row.get('status','unknown')} · {row.get('title','')}")
        return "; ".join(parts)
    if isinstance(value, dict):
        status = str(value.get("status") or "")
        agent = value.get("agent") if isinstance(value.get("agent"), dict) else {}
        result = value.get("result") if isinstance(value.get("result"), dict) else {}
        text = str(result.get("text") or value.get("summary") or "").strip()
        error = str(value.get("error") or "").strip()
        if value.get("workId"):
            agent_name = str(agent.get("name") or "LeadFlow AI agent")
            base = f"BOSS, {agent_name}-kku work delegated. Work ID {value.get('workId')}. Status {status or 'unknown'}."
            if text:
                base += f" Result: {text}"
            if error:
                base += f" Error: {error}"
            return base[:12000]
        return json.dumps(value, ensure_ascii=False)[:12000]
    return str(value)[:12000]


def run(parameters: dict, player=None, session_memory=None) -> str:
    p = parameters or {}
    raw = str(p.get("action") or "").strip().lower()
    action = _ALIASES.get(raw, raw)
    if action not in _ALLOWED:
        return f"Unsupported LeadFlow delegation action: {raw}."
    arguments = p.get("arguments") if isinstance(p.get("arguments"), dict) else {}
    try:
        value = _call(action, arguments)
        return _format(value)
    except Exception as exc:
        message = str(exc)
        if "Unauthorized" in message or "-32001" in message:
            return "LeadFlow delegation endpoint reachable, but the required JARVIS MCP token is missing or invalid."
        if "scope required" in message:
            return f"LeadFlow delegation permission denied: {message}"
        return f"LeadFlow AI delegation failed: {message[:900]}"
