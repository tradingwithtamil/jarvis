---
name: prop-risk-manager
description: Apply BOSS's prop-firm risk, phase targets, recovery and profitable-day logic without breaching firm limits.
keywords: prop firm, risk, drawdown, phase 1, phase 2, funded, profitable days, golden bullet, consistency
---
# Prop Risk Manager
1. Use the account's configured firm/account-type rules as the hard boundary; strategy targets never override firm limits.
2. Forex baseline used in project planning: daily loss 5%, total loss 10%, Phase-1 target 8%, Phase-2 target 5% unless the set file/firm says otherwise.
3. Normal default RR is typically 1:2; project/set-file overrides such as 1:4 are valid only for the intended firm/mode.
4. Golden Bullet may escalate after a loss and restarts after a win; never exceed remaining drawdown/risk allowance.
5. Full Port uses phase-specific risk/target logic and must include configured safety/profit buffers.
6. Profitable Days mode can require repeated daily profit thresholds; one trade/day and stop-after-target are common project rules when enabled.
7. The project's highest-equity PD variant compares the next target against the relevant prior highest balance/equity reference; read the active mode before calculating.
8. Split-runner logic may divide risk across entries/targets; total combined SL risk must equal the intended risk budget.
9. Recovery trades must be sized from remaining allowable drawdown, not from the original account balance blindly.
10. Funded accounts may have stricter per-trade or daily risk guards; block sizing that could breach them.
11. Consistency rules vary by futures firm/account and may be 50/40/35%; calculate against current official rules and live realized profit.
12. Firm payout, buffer, minimum-day and consistency rules change. Verify the latest official FAQ before current eligibility advice.
13. Always state the exact source/config used for risk calculations and never guess a pass/payout status.