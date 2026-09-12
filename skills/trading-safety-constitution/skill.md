---
name: trading-safety-constitution
description: Non-negotiable execution and risk guardrails across Forex, Futures, Stocks and Crypto.
keywords: trading safety risk duplicate stale replay daily loss drawdown one trade signal guard
---
# Trading Safety Constitution
1. One logical signal/trade at a time where the configured strategy requires it; duplicate signal/event guards stay enabled.
2. Reject stale or replayed execution unless BOSS explicitly authorizes replay after evidence review.
3. Never silently increase risk, lot/contracts, leverage, daily loss or max drawdown exposure.
4. Respect account/firm risk limits, session filters, open-trade guards and live-arm state before any broker mutation.
5. Signal generation, execution, SL/TP and close lifecycle must remain correlatable by stable IDs.
