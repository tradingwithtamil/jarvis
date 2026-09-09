---
name: safe-deployment
description: Deploy code changes without overwriting unrelated work or claiming success before verification.
keywords: deploy, deployment, git, pr, merge, release, rollback, verify
---
# Safe Deployment

1. Inspect git status and preserve unrelated uncommitted work.
2. Work from the current canonical base in an isolated branch/worktree when needed.
3. Run syntax checks and targeted tests before commit.
4. Review the diff for accidental secrets, generated files or unrelated changes.
5. Push and merge only the intended change set.
6. Deploy using the existing production path.
7. Verify the deployed version and service health after deployment.
8. Record commit, deployment evidence and rollback point in memory.
