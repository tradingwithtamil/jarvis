---
name: disaster-recovery
description: Recover safely from Mac, VPS, provider, network, config or deployment failure.
keywords: disaster recovery mac vps failover provider outage rollback backup config network github ollama
---
# Disaster Recovery
1. Prefer graceful failover over duplicate active leaders; only one conversational/trading control leader may be authoritative at a time.
2. Mac voice/UI failure: prove heartbeat stale, allow VPS emergency fallback, and demote fallback when Mac primary returns.
3. Provider outage: use configured fallback without changing trading/risk state; report degraded capability honestly.
4. Bad deploy/config: use known-good rollback point, restore config from protected backup, then re-verify production.
5. Never solve an outage by disabling duplicate/risk/security guards globally.
