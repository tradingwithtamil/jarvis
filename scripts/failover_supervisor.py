from __future__ import annotations
import os, signal, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
import psutil
from failover_common import DEFAULT_ROOT, STATE_FILE, atomic_json, brain_key_present, heartbeat_age, load_state

APP_DIR = Path(os.getenv("JARVIS_VPS_APP", str(DEFAULT_ROOT / "app")))
PYTHON = Path(os.getenv("JARVIS_VPS_PYTHON", str(DEFAULT_ROOT / "venv" / "Scripts" / "python.exe")))
LOG_DIR = DEFAULT_ROOT / "logs"
CHECK_SEC = int(os.getenv("JARVIS_FAILOVER_CHECK_SEC", "5"))
STALE_SEC = int(os.getenv("JARVIS_FAILOVER_STALE_SEC", "45"))
STARTUP_GRACE_SEC = int(os.getenv("JARVIS_FAILOVER_STARTUP_GRACE_SEC", "60"))
ENV_FILE = DEFAULT_ROOT / "secrets" / "jarvis.env"


def load_env_file() -> None:
    try:
        for raw in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
    except OSError:
        pass


def pid_alive(pid) -> bool:
    try:
        return bool(pid) and psutil.pid_exists(int(pid)) and psutil.Process(int(pid)).is_running()
    except Exception:
        return False


def update_state(**changes) -> dict:
    state = load_state()
    state.update(changes)
    state["supervisor_utc"] = datetime.now(timezone.utc).isoformat()
    atomic_json(STATE_FILE, state)
    return state


def start_fallback() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = open(LOG_DIR / "jarvis-fallback.log", "a", encoding="utf-8", buffering=1)
    env = os.environ.copy()
    env.update({"JARVIS_HEADLESS": "1", "JARVIS_INSTANCE_ID": "vps-fallback"})
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    proc = subprocess.Popen(
        [str(PYTHON), str(APP_DIR / "main.py"), "--headless"],
        cwd=str(APP_DIR), env=env, stdout=out, stderr=subprocess.STDOUT,
        creationflags=flags,
    )
    update_state(fallback_state="active", fallback_pid=proc.pid, failover_reason="primary_heartbeat_stale")
    return proc.pid


def stop_fallback(pid) -> None:
    if not pid_alive(pid):
        return
    try:
        proc = psutil.Process(int(pid))
        for child in proc.children(recursive=True):
            child.terminate()
        proc.terminate()
        _, alive = psutil.wait_procs([proc], timeout=8)
        for item in alive:
            item.kill()
    except Exception:
        pass


def main() -> None:
    load_env_file()
    started = time.time()
    update_state(fallback_state="standby", fallback_pid=None, supervisor_started_epoch=started)
    while True:
        state = load_state()
        age = heartbeat_age(state)
        fresh_primary = bool(state.get("primary_active")) and age <= STALE_SEC
        pid = state.get("fallback_pid")

        if fresh_primary:
            if pid_alive(pid):
                stop_fallback(pid)
            update_state(fallback_state="standby", fallback_pid=None, failover_reason="primary_healthy")
        elif time.time() - started < STARTUP_GRACE_SEC:
            update_state(fallback_state="startup_grace", fallback_pid=None, failover_reason="startup_grace")
        elif not brain_key_present():
            if pid_alive(pid):
                stop_fallback(pid)
            update_state(fallback_state="blocked_no_brain_key", fallback_pid=None, failover_reason="primary_stale_no_brain_key")
        elif not pid_alive(pid):
            try:
                start_fallback()
            except Exception as exc:
                update_state(fallback_state="start_failed", fallback_pid=None, last_error=repr(exc))
        else:
            update_state(fallback_state="active", fallback_pid=int(pid), failover_reason="primary_heartbeat_stale")
        time.sleep(max(2, CHECK_SEC))


if __name__ == "__main__":
    main()

