---
name: confidence-unknown-policy
description: Separate verified facts from inference and unknowns before acting or reporting.
keywords: confidence verified inferred unknown evidence stale assumption source proof
---
# Confidence Unknown Policy
1. VERIFIED means supported by a fresh authoritative read/tool result or direct deterministic evidence.
2. INFERRED means a reasoned conclusion from evidence but not directly observed; label it when material.
3. UNKNOWN means evidence is missing, stale, inaccessible or contradictory; never convert UNKNOWN into PASS.
4. For high-impact trading/deploy/security decisions, act only on verified prerequisites or ask/stop.
5. Say exactly what evidence is missing when blocked.
