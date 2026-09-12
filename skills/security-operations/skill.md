---
name: security-operations
description: Protect credentials, access, audit trails and production boundaries.
keywords: security secrets credentials tokens keychain hmac ed25519 least privilege audit suspicious ip access
---
# Security Operations
1. Never print, speak, commit or store secrets/tokens/passwords in long-term memory or general logs.
2. Use protected secret stores/environment/OS keychain and least-privilege scoped credentials.
3. Security-sensitive changes require target verification, rollback/recovery consideration and audit evidence.
4. Treat unexpected IP/login/auth changes as an investigation signal; do not bypass controls merely to restore convenience.
5. Public endpoints should use authentication, replay protection and minimal exposed status data.
