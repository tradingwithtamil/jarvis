---
name: stocks-angel-mtf
description: Operate the Stocks specialist with Angel/Upstox portfolio truth, MTF classification and safe execution handling.
keywords: stocks, angel one, upstox, mtf, cnc, delivery, portfolio, holdings, pnl, india
---
# Stocks Angel / MTF Operations
1. Use the existing Stocks specialist and broker-backed data as the source of truth for holdings, orders, positions and P/L.
2. Distinguish DELIVERY/CNC from MTF per symbol; never infer MTF solely from visible invested value.
3. For MTF positions, report own contribution, broker-funded amount, accrued interest, utilized amount and available amount only when broker data provides them.
4. If the broker does not expose a requested MTF field, return UNAVAILABLE rather than estimating.
5. Current portfolio value and P/L must come from the live broker/session source, not cached dashboard text.
6. Pending/rejected/stale orders must retain their real broker status; do not silently convert a rejected order into executed.
7. If the project queue policy says a non-executable order should remain pending for the next eligible session, preserve that state and explain why.
8. Auto-trade/live enablement is a mutation: change it only when BOSS explicitly asks and verify the production read-back.
9. Stocks CRM/dashboard should show classification and funding breakdown when available, with source-proven timestamps.
10. Angel session/gateway health must be checked before blaming strategy logic for missing orders.
11. When using Upstox/other configured stock routes, keep broker-specific fields separate instead of mixing Angel semantics.
12. Never expose broker secrets, session tokens or credentials in memory, logs or replies.
13. For current exchange/broker rules, verify the latest official source before making compliance-sensitive claims.