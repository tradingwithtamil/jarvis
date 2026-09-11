from __future__ import annotations
import hashlib, hmac, json, os, time
from pathlib import Path
import requests

DEFAULT_ROOT = Path(os.getenv("JARVIS_VPS_ROOT", r"C:\JarvisVPS"))
STATE_FILE = DEFAULT_ROOT / "state" / "failover.json"
TOKEN_FILE = DEFAULT_ROOT / "secrets" / "failover.token"
OLLAMA_URL = os.getenv("JARVIS_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("JARVIS_OLLAMA_MODEL", "llama3.2:latest")


def read_token() -> str:
    env = (os.getenv("JARVIS_FAILOVER_TOKEN") or "").strip()
    if env:
        return env
    try:
        return TOKEN_FILE.read_text(encoding="utf-8-sig").strip()
    except OSError:
        return ""


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def sign(body: bytes, token: str) -> str:
    return hmac.new(token.encode("utf-8"), body, hashlib.sha256).hexdigest()


def valid_signature(body: bytes, signature: str, token: str) -> bool:
    if not token or not signature:
        return False
    return hmac.compare_digest(sign(body, token), signature.strip().lower())


def heartbeat_age(state: dict) -> float:
    try:
        return max(0.0, time.time() - float(state.get("last_heartbeat_epoch", 0)))
    except Exception:
        return 1e9


def local_ollama_ready() -> bool:
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        response.raise_for_status()
        models = response.json().get("models") or []
        return any((m.get("name") or m.get("model")) == OLLAMA_MODEL for m in models)
    except Exception:
        return False


def brain_available() -> bool:
    if (os.getenv("OPENAI_API_KEY") or "").strip():
        return True
    if (os.getenv("GEMINI_API_KEY") or "").strip():
        return True
    api_file = DEFAULT_ROOT / "app" / "config" / "api_keys.json"
    try:
        cfg = json.loads(api_file.read_text(encoding="utf-8-sig"))
        if str(cfg.get("openai_api_key") or "").strip() or str(cfg.get("gemini_api_key") or "").strip():
            return True
    except Exception:
        pass
    return local_ollama_ready()


def brain_key_present() -> bool:
    return brain_available()
