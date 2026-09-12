---
name: cost-optimizer
description: Control OpenAI, Gemini, Make and infrastructure usage without degrading required safety.
keywords: cost credits openai gemini make operations polling tokens api usage optimize batch watchdog
---
# Cost Optimizer
1. Prefer event-driven or batched health checks over frequent polling when the underlying condition changes slowly.
2. Use lightweight/read-only checks for routine health and reserve expensive reasoning/deep audits for anomalies or BOSS requests.
3. Avoid duplicate provider calls, duplicate screenshots, repeated retries and parallel scenarios that answer the same question.
4. Trading execution latency/safety outranks marginal cost savings; never delay required protective actions to save credits.
5. When usage spikes, identify scenario/module/request counts before blaming a component.
