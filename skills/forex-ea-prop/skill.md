---
name: forex-ea-prop
description: Operate the Dark Flow MT5 EA, account series, prop phases, PD mode and risk controls safely.
keywords: forex, mt5, ea, prop firm, phase 1, phase 2, funded, profitable days, golden bullet, full port
---
# Forex EA and Prop Operations
1. Core route is TradingView signal -> Telegram/IOT route -> MT5 EA. Start trading only from a new signal after enable.
2. Entry requires HTF zone tap plus 1m MSS/BOS confirmation in the same direction. Pending confirmation may expire after configured bars.
3. Entry modes include Market, 50% retrace and 1m OB/FVG limit. SL can use TF fractal, fixed distance or 1m fractal; RR is configurable.
4. Enforce daily loss, total/max loss, daily equity lock, session/no-trade filters, timeframe filter and one-trade-only settings.
5. Phase-1, Phase-2 and Funded are separate account series, up to 10 accounts each; the same valid signal can execute across active series simultaneously.
6. Rotation must skip missing/inactive slots, continue A1..A10, reset locks on the next broker day and never hedge inside the same series.
7. Normal mode uses configured fixed risk/RR. Golden Bullet escalates after loss and restarts after a win. Full Port uses phase-specific risk and target logic.
8. Profitable Days mode is normally OFF unless enabled. Typical rule: one trade/day, 1:1, complete configured profitable days; stop trading after the daily PD target is achieved.
9. Highest-equity PD logic compares the new target against prior highest/equity rule configured for that account; do not guess which PD mode is active.
10. Funded risk guards and firm-specific limits override strategy sizing. Prevent an order that would breach the configured risk rule.
11. Set files are organized by phase, balance, account slot and mode; preserve existing folder/version conventions when updating.
12. Current EA/version, prop-firm rules and live account state must be read from production before claiming a change or pass status.
13. Never replay an old signal, duplicate an order, change risk, or arm live trading unless BOSS explicitly authorizes it.