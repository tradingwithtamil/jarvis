---
name: production-audit
description: Verify the real live state before claiming a system, deploy or trade route is complete.
keywords: production, audit, verify, health, live, evidence, status
---
# Production Audit

1. Read the canonical production endpoint/service first.
2. Confirm version or commit identity when available.
3. Check process/service health and recent errors.
4. Verify the actual execution route and required dependencies.
5. Compare configured state with runtime state.
6. Never treat queued, pending, staged or local-only work as completed.
7. If a check cannot be performed, mark that item UNVERIFIED instead of guessing.
8. Return concrete evidence and the smallest next action for any blocker.
