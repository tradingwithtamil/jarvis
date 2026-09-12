---
name: change-management
description: Apply production changes with backup, tests, deployment proof and rollback safety.
keywords: change management git backup diff compile test deploy rollback version production
---
# Change Management
1. Inspect current branch/status/version and preserve unrelated local custom work before editing.
2. Create a backup or isolated worktree for risky changes; never overwrite a dirty production tree blindly.
3. Patch narrowly, run syntax/compile/unit checks available to the project, then inspect diff for secrets/unintended edits.
4. Deploy only to the intended target, then read back version/health and perform fresh functional proof.
5. Keep a rollback point and never call COMPLETE from a successful build alone.
