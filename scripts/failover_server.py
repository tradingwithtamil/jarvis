from __future__ import annotations
import asyncio, json, os, time
from datetime import datetime, timezone
import requests
from fastapi import FastAPI, Header, HTTPException, Request
import uvicorn
from failover_common import STATE_FILE, atomic_json, heartbeat_age, load_state, read_token, valid_signature

HOST = os.getenv("JARVIS_FAILOVER_HOST", "0.0.0.0")
PORT = int(os.getenv("JARVIS_FAILOVER_PORT", "8789"))
MAX_SKEW = int(os.getenv("JARVIS_HEARTBEAT_MAX_SKEW", "120"))
STALE_SEC = int(os.getenv("JARVIS_FAILOVER_STALE_SEC", "45"))
OLLAMA_URL = os.getenv("JARVIS_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("JARVIS_OLLAMA_MODEL", "llama3.2:latest")

app = FastAPI(title="Jarvis Failover Heartbeat", docs_url=None, redoc_url=None)


def _signed_json(body: bytes, signature: str) -> dict:
    token = read_token()
    if not valid_signature(body, signature, token):
        raise HTTPException(status_code=401, detail="invalid_signature")
    try:
        payload = json.loads(body.decode("utf-8"))
        sent = float(payload["epoch"])
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_payload")
    if abs(time.time() - sent) > MAX_SKEW:
        raise HTTPException(status_code=409, detail="stale_request")
    return payload


def _ollama_ready() -> bool:
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        response.raise_for_status()
        models = response.json().get("models") or []
        return any((m.get("name") or m.get("model")) == OLLAMA_MODEL for m in models)
    except Exception:
        return False


def _ollama_chat(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are Jarvis, a concise emergency assistant. Address the owner as BOSS."},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "keep_alive": -1,
        "options": {"num_predict": 220},
    }
    response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=90)
    response.raise_for_status()
    return str((response.json().get("message") or {}).get("content") or "").strip()


@app.post("/v1/heartbeat")
async def heartbeat(request: Request, x_jarvis_signature: str = Header(default="")):
    body = await request.body()
    payload = _signed_json(body, x_jarvis_signature)
    state = load_state()
    state.update({
        "last_heartbeat_epoch": time.time(),
        "last_heartbeat_utc": datetime.now(timezone.utc).isoformat(),
        "primary_instance": str(payload.get("instance") or "mac"),
        "primary_active": bool(payload.get("active", True)),
        "primary_version": str(payload.get("version") or ""),
        "heartbeat_source": request.client.host if request.client else "unknown",
    })
    atomic_json(STATE_FILE, state)
    return {"ok": True, "mode": "primary_seen", "age": 0}


@app.post("/v1/fallback/chat")
async def fallback_chat(request: Request, x_jarvis_signature: str = Header(default="")):
    body = await request.body()
    payload = _signed_json(body, x_jarvis_signature)
    state = load_state()
    age = heartbeat_age(state)
    primary_fresh = bool(state.get("primary_active")) and age <= STALE_SEC
    if primary_fresh or state.get("fallback_state") != "active":
        raise HTTPException(status_code=409, detail="fallback_not_active")
    prompt = str(payload.get("prompt") or "").strip()
    if not prompt or len(prompt) > 8000:
        raise HTTPException(status_code=400, detail="invalid_prompt")
    try:
        answer = await asyncio.to_thread(_ollama_chat, prompt)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"ollama_unavailable:{type(exc).__name__}")
    return {"ok": True, "mode": "vps_ollama", "model": OLLAMA_MODEL, "answer": answer}


@app.get("/v1/status")
def status():
    state = load_state()
    return {
        "ok": True,
        "primary_active": bool(state.get("primary_active")),
        "heartbeat_age_sec": round(heartbeat_age(state), 1),
        "fallback_state": state.get("fallback_state", "unknown"),
        "fallback_pid": state.get("fallback_pid"),
        "fallback_provider": "ollama_local" if state.get("fallback_state") == "active" else None,
        "ollama_ready": _ollama_ready(),
        "ollama_model": OLLAMA_MODEL,
    }


if __name__ == "__main__":
    if not read_token():
        raise SystemExit("JARVIS_FAILOVER_TOKEN missing")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
