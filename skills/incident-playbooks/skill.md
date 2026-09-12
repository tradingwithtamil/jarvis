---
name: incident-playbooks
description: Diagnose trading and automation incidents end-to-end before changing production.
keywords: incident stale signal no trade duplicate sl tp api 401 429 500 heartbeat telemetry make ea
---
# Incident Playbooks
1. Start with symptom + timestamp + correlation/signal ID + owning domain.
2. Trace ingress -> router -> risk guard -> broker/order -> fill -> SL/TP -> lifecycle writer -> CRM/alerts.
3. For no-trade: prove whether signal arrived, passed freshness/duplicate/risk/session guards, reached broker, and got an order/fill response.
4. For stale/telemetry: compare producer timestamp, transport, writer and consumer read freshness.
5. Fix the narrowest proven fault, preserve trade safety, then rerun a harmless or explicitly authorized functional proof.
