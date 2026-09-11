from __future__ import annotations
import hashlib, hmac, json, os, threading, time
from pathlib import Path
from urllib.request import Request, urlopen


def _settings(base_dir: Path) -> tuple[str, str]:
    url = (os.getenv("JARVIS_VPS_HEARTBEAT_URL") or "").strip()
    token = (os.getenv("JARVIS_FAILOVER_TOKEN") or "").strip()
    if url and token:
        return url, token
    try:
        cfg = json.loads((base_dir / "config" / "api_keys.json").read_text(encoding="utf-8-sig"))
        url = url or str(cfg.get("failover_heartbeat_url") or "").strip()
        token = token or str(cfg.get("failover_token") or "").strip()
    except Exception:
        pass
    return url, token


def _send(url: str, token: str, instance: str) -> None:
    body = json.dumps({"epoch": time.time(), "instance": instance, "active": True}, separators=(",", ":")).encode()
    sig = hmac.new(token.encode(), body, hashlib.sha256).hexdigest()
    req = Request(url, data=body, method="POST", headers={"Content-Type": "application/json", "X-Jarvis-Signature": sig})
    with urlopen(req, timeout=5) as response:
        response.read(256)


def start_mac_heartbeat(base_dir: Path, interval: int = 10) -> bool:
    url, token = _settings(base_dir)
    if not url or not token:
        return False
    instance = os.getenv("JARVIS_INSTANCE_ID", "mac-primary")

    def _loop():
        failures = 0
        while True:
            try:
                _send(url, token, instance)
                failures = 0
            except Exception as exc:
                failures += 1
                if failures in (1, 6, 30):
                    print(f"[Failover] heartbeat unavailable ({type(exc).__name__})")
            time.sleep(max(5, interval))

    threading.Thread(target=_loop, name="jarvis-failover-heartbeat", daemon=True).start()
    return True
