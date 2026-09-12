---
name: make-self-heal
description: Keep Make.com automation healthy with low-credit daily checks, staggered schedules and safe repair rules.
keywords: make, self heal, watchdog, credits, scheduler, daily, forex, futures, stocks, crypto
---
# Make Self-Heal / Watchdog
1. Trading webhooks remain immediate; health/self-heal checks run separately.
2. Default project preference is one self-heal/watchdog run per day unless BOSS explicitly requests a different cadence.
3. Stagger Forex, Stocks, Futures and Crypto checks to avoid overlap; preserve the configured per-system windows.
4. Do not use high-frequency polling such as every 5 seconds for routine health checks when a daily check is sufficient.
5. Measure Make credits from actual scenario executions/modules/retries before blaming a specific poller.
6. Self-heal can verify routes, adapters, connector/session health, scheduler state and known safe service restarts.
7. It must not replay signals, place trades, change risk, arm live trading or alter broker state unless explicitly authorized.
8. When a read adapter is missing, report the exact blocker instead of marking the specialist healthy from assumptions.
9. After a repair, verify the relevant scenario/task status and one harmless read path before calling it complete.
10. Keep domain schedules and scenario names in their owning specialist project; CEO only orchestrates and audits them.
11. Prefer idempotent repairs and duplicate guards so rerunning a watchdog cannot create duplicate work.
12. Report daily credit expectation as an estimate only when module counts are known; otherwise label it UNKNOWN.
13. Never store Make secrets/webhook secrets in Jarvis memory.