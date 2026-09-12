---
name: account-prop-registry
description: Maintain account/prop metadata safely and verify changing firm rules before action.
keywords: account prop firm phase challenge funded registry rules target drawdown consistency payout
---
# Account Prop Registry
1. Registry may store firm, account size, phase, slot, strategy/risk mode and non-secret routing identifiers.
2. Do not store passwords, API secrets, full sensitive credentials or temporary balances in long-term knowledge.
3. Firm targets, drawdown, consistency, payout/minimum-day and restricted-strategy rules are changeable: verify current official FAQ/rules before risk or payout decisions.
4. Separate user-configured rules from firm-enforced rules and label both.
5. Account state must come from live broker/CRM reads when available; registry is metadata, not live truth.
