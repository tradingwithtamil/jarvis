---
name: source-of-truth
description: Resolve conflicting CRM, broker, EA, Make, logs and dashboard evidence.
keywords: source truth evidence conflict crm broker ea make telemetry timestamp provenance
---
# Source Of Truth
1. Prefer the most direct production source for the fact being asked: broker for fills/positions, EA for local execution intent/state, CRM for persisted lifecycle, Make for scenario execution, Git for source/deploy version.
2. Use fresh timestamps and correlation IDs; stale screenshots or cached dashboards never overrule newer direct evidence.
3. If sources disagree, state the disagreement and trace the lifecycle instead of choosing a convenient answer.
4. Use VERIFIED / INFERRED / UNKNOWN internally; only VERIFIED may support a completed production claim.
5. Current status questions require a fresh read, not memory.
