from __future__ import annotations
import json, os, time
from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException, Request
import uvicorn
from failover_common import STATE_FILE, atomic_json, heartbeat_age, load_state, read_token, valid_signature

HOST = os.getenv("JARVIS_FAILOVER_HOST", "0.0.0.0")
PORT = int(os.getenv("JARVIS_FAILOVER_PORT", "8789"))
MAX_SKEW = int(os.getenv("JARVIS_HEARTBEAT_MAX_SKEW", "120"))

app = FastAPI(title="Jarvis Failover Heartbeat", docs_url=None, redoc_url=None)


@app.post("/v1/heartbeat")
async def heartbeat(request: Request, x_jarvis_signature: str = Header(default="")):
    token = read_token()
    body = await request.body()
    if not valid_signature(body, x_jarvis_signature, token):
        raise HTTPException(status_code=401, detail="invalid_signature")
    try:
        payload = json.loads(body.decode("utf-8"))
        sent = float(payload["epoch"])
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_payload")
    if abs(time.time() - sent) > MAX_SKEW:
        raise HTTPException(status_code=409, detail="stale_heartbeat")
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


@app.get("/v1/status")
def status():
    state = load_state()
    return {
        "ok": True,
        "primary_active": bool(state.get("primary_active")),
        "heartbeat_age_sec": round(heartbeat_age(state), 1),
        "fallback_state": state.get("fallback_state", "unknown"),
        "fallback_pid": state.get("fallback_pid"),
    }


if __name__ == "__main__":
    if not read_token():
        raise SystemExit("JARVIS_FAILOVER_TOKEN missing")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
