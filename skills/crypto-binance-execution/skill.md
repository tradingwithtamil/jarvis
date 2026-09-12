---
name: crypto-binance-execution
description: Run Dark Flow Crypto/Binance execution with lifecycle, duplicate guards and source-proven trade state.
keywords: crypto, binance, btcusdt, spot, execution, fills, lifecycle, stop loss, take profit
---
# Crypto Binance Execution
1. Use the existing Crypto specialist/API route; do not create a second parallel execution path.
2. Primary project use is Binance Spot with configured TradingView/brain signals and one active signal/trade policy unless BOSS changes it.
3. Every execution must bind a durable signal UID to the broker/order identifiers and persist strategy/account context.
4. Save open-time entry, quantity, SL/TP intent and actual exchange acknowledgements; update fills and close reason from exchange truth.
5. Duplicate guard must prevent the same SignalID+event from opening twice, including retries and webhook redelivery.
6. Before sending, validate symbol, side, quantity/minimums, available balance, precision and current execution eligibility.
7. Never report TP/SL or fill values that Binance did not confirm; requested values and actual values must remain distinguishable.
8. Trade history/lifecycle should expose signal_uid, order_id, strategy_id, entry, SL, TP, fill, close reason and timestamps where available.
9. Self-heal/watchdog may repair routing/connector health, but must never replay a signal or mutate trading risk by itself.
10. If Binance/API/session health is unavailable, return BLOCKED/UNAVAILABLE rather than guessing current trade state.
11. Preserve spot semantics; do not assume futures/leverage behavior unless the configured route explicitly says so.
12. Current balances, positions, fees and exchange rules must be read live when needed.
13. Never store or expose Binance API secrets in Jarvis long-term memory or skill files.