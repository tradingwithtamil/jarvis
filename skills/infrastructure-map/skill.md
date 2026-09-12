---
name: infrastructure-map
description: Know Dark Flow/JARVIS system boundaries, dependencies and ownership without exposing secrets.
keywords: infrastructure mac vps cloudflare github make mt5 telegram binance tradovate crosstrade crm api dependency
---
# Infrastructure Map
1. Mac is the primary local voice/UI node; Windows VPS is standby/failover and production support node.
2. JARVIS coordinates existing specialist systems; it must not casually create duplicate parallel control planes.
3. FOREX owns MT5 EA/series execution; FUTURES owns CrossTrade/Tradovate routing; STOCKS owns broker/portfolio/MTF; CRYPTO owns Binance/execution lifecycle.
4. CEO/CRM health is an observability/control layer, not a substitute for broker source truth.
5. Secrets and exact credentials belong in protected stores, never in skill text, memory, logs or Git.
