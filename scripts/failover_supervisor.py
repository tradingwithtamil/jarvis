from __future__ import annotations
import os, time
from datetime import datetime, timezone
from pathlib import Path
import psutil
from failover_common import DEFAULT_ROOT, STATE_FILE, atomic_json, brain_available, heartbeat_age, load_state

CHECK_SEC = int(os.getenv("JARVIS_FAILOVER_CHECK_SEC", "5"))
STALE_SEC = int(os.getenv("JARVIS_FAILOVER_STALE_SEC", "45"))
STARTUP_GRACE_SEC = int(os.getenv("JARVIS_FAILOVER_STARTUP_GRACE_SEC", "20"))
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


def stop_legacy_fallback(pid) -> None:
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


def update_state(**changes) -> dict:
    state = load_state()
    state.update(changes)
    state["supervisor_utc"] = datetime.now(timezone.utc).isoformat()
    atomic_json(STATE_FILE, state)
    return state


def main() -> None:
    load_env_file()
    started = time.time()
    prior = load_state()
    legacy_pid = prior.get("fallback_pid")
    if pid_alive(legacy_pid):
        stop_legacy_fallback(legacy_pid)
    update_state(fallback_state="standby", fallback_pid=None, supervisor_started_epoch=started)
    while True:
        state = load_state()
        age = heartbeat_age(state)
        fresh_primary = bool(state.get("primary_active")) and age <= STALE_SEC

        if fresh_primary:
            update_state(
                fallback_state="standby",
                fallback_pid=None,
                failover_reason="primary_healthy",
                fallback_provider=None,
            )
        elif time.time() - started < STARTUP_GRACE_SEC:
            update_state(
                fallback_state="startup_grace",
                fallback_pid=None,
                failover_reason="startup_grace",
                fallback_provider=None,
            )
        elif not brain_available():
            update_state(
                fallback_state="blocked_no_brain",
                fallback_pid=None,
                failover_reason="primary_stale_no_brain",
                fallback_provider=None,
            )
        else:
            update_state(
                fallback_state="active",
                fallback_pid=None,
                failover_reason="primary_heartbeat_stale",
                fallback_provider="ollama_local",
            )
        time.sleep(max(2, CHECK_SEC))


if __name__ == "__main__":
    main()
