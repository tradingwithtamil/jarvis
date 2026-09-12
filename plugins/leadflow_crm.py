"""LeadFlow CRM MCP bridge for JARVIS."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import urllib.error
import urllib.request
import uuid

_READ_ACTIONS = {
    "list_agents", "list_departments", "search_knowledge", "list_training_sources",
    "list_users", "list_leads", "get_lead", "list_contacts", "list_tasks",
    "list_whatsapp_conversations", "get_whatsapp_messages", "list_followups",
    "list_appointments", "list_tickets", "today_new_leads",
}
_WRITE_ACTIONS = {
    "create_agent_draft", "update_agent_draft", "add_approved_knowledge",
    "create_lead", "update_lead", "delete_lead", "upsert_contact",
    "create_task", "update_task", "delete_task", "send_whatsapp_reply",
    "create_followup", "update_followup", "create_appointment", "update_appointment",
    "create_ticket", "update_ticket", "add_lead_note", "assign_lead",
    "update_pipeline_stage",
}
_EVALUATE_ACTIONS = {"run_evaluation"}
_ALLOWED = {"health"} | _READ_ACTIONS | _WRITE_ACTIONS | _EVALUATE_ACTIONS
PLUGIN = {
    "name": "leadflow_crm",
    "description": (
        "Operate LeadFlow CRM. Read leads, contacts, tasks, WhatsApp, follow-ups, "
        "appointments, tickets and AI Workforce data. For questions like 'any new leads today?', "
        "'today leads?' or 'innaiku new lead vandhiruka?', use action today_new_leads. "
        "Create/update CRM records and send official WhatsApp replies only when the selected action permits it."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "LeadFlow action/tool name."},
            "arguments": {
                "type": "OBJECT",
                "description": "Arguments for the selected LeadFlow action.",
                "properties": {
                    "query": {"type": "STRING"}, "leadId": {"type": "STRING"},
                    "contactId": {"type": "STRING"}, "conversationId": {"type": "STRING"},
                    "taskId": {"type": "STRING"}, "followupId": {"type": "STRING"},
                    "appointmentId": {"type": "STRING"}, "ticketId": {"type": "STRING"},
                    "userId": {"type": "STRING"}, "assignedUserId": {"type": "STRING"},
                    "name": {"type": "STRING"}, "phone": {"type": "STRING"},
                    "email": {"type": "STRING"}, "text": {"type": "STRING"},
                    "title": {"type": "STRING"}, "description": {"type": "STRING"},
                    "notes": {"type": "STRING"}, "status": {"type": "STRING"},
                    "stage": {"type": "STRING"}, "source": {"type": "STRING"},
                    "campaign": {"type": "STRING"}, "priority": {"type": "STRING"},
                    "dueAt": {"type": "STRING"}, "scheduledAt": {"type": "STRING"},
                    "startTime": {"type": "STRING"}, "endTime": {"type": "STRING"},
                    "confirmed": {"type": "BOOLEAN"}, "limit": {"type": "NUMBER"},
                    "timezone": {"type": "STRING", "description": "IANA timezone for date-based reads; defaults to Asia/Dubai."}
                },
            },
        },
        "required": ["action"],
    },
}
def _endpoint() -> str:
    return os.getenv("LEADFLOW_MCP_URL", "").strip()


def _read_token() -> str:
    return os.getenv("LEADFLOW_MCP_TOKEN", "").strip()


def _admin_token() -> str:
    return os.getenv("LEADFLOW_MCP_ADMIN_TOKEN", "").strip()


def _token_for(action: str) -> str:
    if action in _WRITE_ACTIONS or action in _EVALUATE_ACTIONS:
        token = _admin_token()
        if not token:
            raise RuntimeError("LeadFlow admin MCP token is not configured in JARVIS Keychain.")
        return token
    token = _read_token() or _admin_token()
    if not token:
        raise RuntimeError("LeadFlow MCP token is not configured in JARVIS Keychain.")
    return token


def _headers(token: str = "") -> dict[str, str]:
    h = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/152.0 Safari/537.36",
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _post(body: dict, token: str) -> dict:
    url = _endpoint()
    if not url.startswith("https://"):
        raise RuntimeError("LEADFLOW_MCP_URL must be configured with HTTPS.")
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), headers=_headers(token), method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read(1_048_576).decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read(2048).decode("utf-8", errors="replace")
        raise RuntimeError(f"LeadFlow MCP HTTP {e.code}: {detail[:300]}") from e


def _tool_call(name: str, arguments: dict | None = None):
    token = _token_for(name)
    body = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}},
    }
    payload = _post(body, token)
    if payload.get("error"):
        raise RuntimeError(str(payload["error"].get("message") or "LeadFlow MCP error"))
    result = payload.get("result") or {}
    if "structuredContent" in result:
        return result["structuredContent"]
    content = result.get("content") or []
    if content and isinstance(content[0], dict):
        value = content[0].get("text")
        try:
            return json.loads(value)
        except Exception:
            return value
    return result


def _parse_created_at(value):
    if not value:
        return None
    try:
        text = str(value).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _today_new_leads(arguments: dict) -> str:
    tz_name = str(arguments.get("timezone") or os.getenv("LEADFLOW_TIMEZONE") or "Asia/Dubai").strip()
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz_name = "Asia/Dubai"
        tz = ZoneInfo(tz_name)
    try:
        requested_limit = int(arguments.get("limit") or 500)
    except Exception:
        requested_limit = 500
    query = {"limit": max(1, min(requested_limit, 1000))}
    for key in ("status", "source"):
        if arguments.get(key):
            query[key] = arguments[key]
    rows = _tool_call("list_leads", query)
    if not isinstance(rows, list):
        return "LeadFlow returned an unexpected leads response."
    today = datetime.now(tz).date()
    matches = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        created = _parse_created_at(row.get("created_at"))
        if created and created.astimezone(tz).date() == today:
            matches.append((created, row))
    matches.sort(key=lambda item: item[0], reverse=True)
    if not matches:
        return f"BOSS, {today.isoformat()} ({tz_name}) today LeadFlow CRM-la new leads 0."
    details = []
    for created, row in matches[:10]:
        name = str(row.get("name") or "Unnamed lead")
        source = str(row.get("source") or "Unknown source")
        status = str(row.get("status") or "")
        local_time = created.astimezone(tz).strftime("%H:%M")
        details.append(" · ".join(x for x in (name, source, status, local_time) if x))
    extra = f" Plus {len(matches)-10} more." if len(matches) > 10 else ""
    return f"BOSS, today LeadFlow CRM-la {len(matches)} new lead{'s' if len(matches) != 1 else ''} vandhirukku: " + "; ".join(details) + extra


def _compact(value) -> str:
    if isinstance(value, list):
        if not value:
            return "No matching LeadFlow records."
        rows = []
        for item in value[:20]:
            if isinstance(item, dict):
                label = (
                    item.get("name") or item.get("title") or item.get("subject")
                    or item.get("ticket_number") or item.get("display_name") or item.get("id")
                )
                status = item.get("status") or item.get("conversation_status") or ""
                extra = item.get("phone") or item.get("role") or item.get("assigned_to") or ""
                rows.append(" · ".join(str(x) for x in (label, extra, status) if x))
            else:
                rows.append(str(item))
        suffix = f" Plus {len(value)-20} more." if len(value) > 20 else ""
        return "; ".join(rows) + suffix
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)[:12000]
    return str(value)[:12000]


def run(parameters: dict, player=None, session_memory=None) -> str:
    p = parameters or {}
    action = str(p.get("action") or "").strip().lower()
    if action not in _ALLOWED:
        return "Unsupported LeadFlow action."
    try:
        if action == "health":
            base = _endpoint().split("/api/mcp/leadflow", 1)[0]
            req = urllib.request.Request(base + "/api/health", headers=_headers(), method="GET")
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read(65536).decode("utf-8"))
            return f"LeadFlow CRM health {'OK' if data.get('ok') else 'not ready'}. Database {data.get('database','unknown')}."
        args = p.get("arguments") if isinstance(p.get("arguments"), dict) else {}
        if action == "today_new_leads":
            return _today_new_leads(args)
        value = _tool_call(action, args)
        return _compact(value)
    except Exception as exc:
        message = str(exc)
        if "Unauthorized" in message or "-32001" in message:
            return "LeadFlow CRM is reachable, but the required JARVIS MCP token is missing or invalid."
        if "scope required" in message:
            return f"LeadFlow permission denied for this action: {message}"
        return f"LeadFlow CRM request failed: {message[:700]}"
