---
name: incident-recovery
description: Diagnose stuck, stale, rejected or failed workflows and restore the existing route safely.
keywords: incident, stale, stuck, failed, rejected, recovery, diagnose, retry
---
# Incident Recovery

1. Capture the exact failing state, timestamp and error before changing anything.
2. Trace the request through the existing route from source to final dependency.
3. Separate data/state errors from connectivity, authorization and code defects.
4. Fix the earliest proven root cause rather than adding retries around an unknown failure.
5. Preserve idempotency and duplicate guards before replaying work.
6. Re-run only safe affected operations; never silently replay trading mutations.
7. Verify recovery from production evidence, then check for recurrence.
8. Save root cause, fix and prevention note in Jarvis memory.
