---
name: trade-lifecycle-audit
description: Audit every trade from signal to close with durable IDs, SL/TP snapshots and source-proven execution evidence.
keywords: trade lifecycle, audit, signal uid, order id, strategy id, fill, sl, tp, close reason, telemetry
---
# Trade Lifecycle Audit
1. Treat signal -> decision -> order -> fill -> open position -> SL/TP changes -> close as one traceable lifecycle.
2. Persist signal_uid at decision/execution time and bind it to order/ticket/position IDs; never backfill by guessing.
3. Persist strategy_id, platform, account/series, symbol, side, timeframe and signal timestamp.
4. Save requested entry/SL/TP and actual broker/exchange values separately when they differ.
5. Open-time SL/TP snapshots must survive later position updates so the original risk intent remains auditable.
6. Close records should include close price, P/L, fees where available, close_reason and broker close identifiers.
7. LAST_EXECUTED_TRADE must be derived from persisted lifecycle truth, not reconstructed from partial dashboard fields.
8. Null signal_uid/order_id/SL/TP on old historical trades does not prove a new writer is broken; test with a new post-deploy signal.
9. Never invent historical UIDs or exact fills to make an audit look complete.
10. A deployment is verified only when a fresh post-deploy trade carries the expected lifecycle fields end to end.
11. Keep Forex, Futures, Stocks and Crypto field mappings explicit; broker identifiers are not interchangeable.
12. Report PASS/FAIL/UNKNOWN per field and identify the source used for each conclusion.
13. Never mutate or replay a trade merely to satisfy an audit unless BOSS explicitly authorizes a controlled test.