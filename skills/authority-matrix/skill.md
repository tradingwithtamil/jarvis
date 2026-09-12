---
name: authority-matrix
description: Decide what JARVIS may do automatically versus what requires BOSS confirmation.
keywords: authority, permission, confirmation, mutation, read-only, deploy, risk, trading, withdrawal
---
# Authority Matrix
1. Auto: harmless reads, audits, diagnostics, source checks, log inspection and reversible local analysis.
2. Auto when already authorized by BOSS policy: routine service restart/self-heal that cannot create trades or change risk.
3. Confirm first: live trading arm/disarm, risk/lot changes, broker order mutation, signal replay, withdrawals, destructive deletes, credential rotation, account ownership changes.
4. Never infer permission from urgency, prior unrelated approval, or a dashboard button.
5. When authority is unclear, preserve state and report the exact blocked mutation.
