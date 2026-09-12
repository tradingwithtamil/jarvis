---
name: futures-prop-automation
description: Run Dark Flow futures automation through CrossTrade/Tradovate with challenge/funded prop controls.
keywords: futures, crosstrade, tradovate, apex, lucid, topstep, challenge, funded, contracts, micro
---
# Futures Prop Automation
1. Core route is TradingView -> Make -> CrossTrade -> Tradovate; keep the existing specialist route instead of creating duplicates.
2. Futures phases are Challenge and Funded. PD mode is not part of the standard futures flow.
3. Use micro contracts where configured; convert risk/lot intent into contracts using current instrument value and firm limits.
4. One trade at a time by default. If an account already has an open trade, skip/hold the next signal according to configured queue policy.
5. Support split execution when required, with consistent SL/TP and contract totals; re-check slippage and minimum-contract fallback before sending.
6. Challenge/Funded account rotation must use only active configured accounts and preserve series order.
7. DFT, No-Wick and Breakout may route to separate account groups/webhooks; never cross-wire strategies without source proof.
8. Store/update balance, equity, open positions, target, drawdown and trade outcome after execution; alerts go to Telegram when configured thresholds are hit.
9. Consistency controls may be 50/40/35 percent depending on the firm/account; funded progression rules can require profit days before switching modes.
10. Firms in the project include Apex, Lucid and Topstep plus newer configured firms; never assume their current rules from memory.
11. Before sizing or payout/pass advice, verify the exact current FAQ/account type because drawdown, consistency, buffers and payout rules can change.
12. Never claim a futures order executed until Tradovate/CrossTrade source evidence confirms account, contract, side, fill and protective orders.
13. Preserve Challenge vs Funded separation and never mutate risk/live settings unless BOSS explicitly requests it.