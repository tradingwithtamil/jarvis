---
name: memory-policy
description: Store stable useful context while excluding secrets and fast-changing production state.
keywords: memory stable temporary secret token balance live status preference architecture forget update
---
# Memory Policy
1. Long-term memory is for stable preferences, architecture, operating rules, goals and durable project decisions.
2. Do not persist API keys, passwords, session tokens, private auth material, one-time codes or sensitive credential values.
3. Do not persist temporary balances, current health, transient incidents, current prices or other fast-changing facts as durable truth.
4. When BOSS corrects a stable fact, latest explicit correction wins and conflicting old memory should be updated rather than duplicated.
5. Current-state answers must query live sources even when memory contains historical context.
