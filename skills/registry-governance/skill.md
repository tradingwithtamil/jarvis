---
name: registry-governance
description: Keep infrastructure/account registries useful without letting them become stale source truth.
keywords: registry metadata inventory version freshness owner source url account firm service dependency
---
# Registry Governance
1. Every registry item should identify owner/domain, purpose, canonical source and whether the field is static metadata or live state.
2. Static metadata may be cached; live balances, open positions, current health and changing firm rules must be refreshed at use time.
3. Unknown values stay null/unknown rather than guessed.
4. Remove or supersede deprecated routes explicitly so JARVIS does not choose old endpoints by name similarity.
5. Registries must contain no secret values.
