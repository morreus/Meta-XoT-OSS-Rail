---
name: 60-commit
description: Create one atomic, conventional git commit — inspects the real diff, scans for secrets, assesses risk, requires reviews/tests green, and asks before committing. Run last.
disable-model-invocation: true
argument-hint: <scope / summary of the change>
---

Create a git commit for: $ARGUMENTS

## PHASE 0: Pre-commit gate (MANDATORY)
- Reviews for this change are **clean** (no open High/Med) and tests are **green** (per `${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md`). If reviews/tests are red, suspicious, or missing → **STOP and warn the user; do not commit** unless they explicitly waive.
- Read `CLAUDE.md` for protected/irreversible files and secret-handling rules.

## PHASE 1: Inspect changes (no assumptions)
Run and actually read: `git status`, `git diff`, `git diff --staged`, `git diff --stat`.
- **If nothing to commit → STOP and tell the user.**
- Note files/functions changed, new deps, config changes.

## PHASE 2: Secret scan (MANDATORY — blocks the commit)
Scan the diff for secrets BEFORE proposing anything: `.env` contents, API keys/tokens, passwords, private keys, connection strings, and any project-specific secret names from CLAUDE.md (e.g. `PAYMENTS_API_KEY`). If ANY appear in the diff → **STOP, do NOT commit**, warn the user, and tell them to remove (and rotate) the secret. Never commit secrets.

## PHASE 3: Risk + scope
- **Risk assessment** — pull from `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md` risk checklist + the context map's **Project-Risk Touchpoints**. Flag High/Med risks: breaking public API or data/schema, irreversible/production impact, precision/time-series leakage, serialization/save-format changes — whatever applies to this stack/project.
- **Protected files** — if the diff touches a file CLAUDE.md flags as protected/irreversible (e.g. a production data file), require its **backup ritual first** and warn before committing.
- **Scope check** — is this one logical unit of work? Any unrelated "while I'm here" edits? If mixed → propose splitting into multiple commits.

## PHASE 4: Propose the commit (Conventional Commits)
```
<type>(<scope>): <summary>        # ≤72 chars, imperative mood, no trailing period
Why: <motivation/context>
What: <brief description of the change>
How verified: <the stack's verification — tests run, script output, Editor checks>
Risk: <edge cases, known limitations>
Refs: <the plan document> | #issue
```
Types: `feat` / `fix` / `refactor` / `perf` / `test` / `docs` / `chore` / `style`. Scope = affected area.

Present the proposed message + the exact file list. **Wait for approval: yes / edit / split / abort.**

## PHASE 5: Commit (only after approval)
Stage the intended files (`git add <files>`; use `-A` only if every change belongs in this commit) and commit with the multi-line message. Do NOT add a co-authored-by footer unless the user asks. (Destructive git — amend/rebase/reset/force-push — triggers a confirmation prompt to the operator; don't attempt it.)

## PHASE 6: Post-commit
Show the hash, branch, and files committed. Offer next steps (push / open PR) but do NOT push automatically.

## RULES
1. Read the real diff — no assumptions.
2. **Never commit** with red reviews/tests, with secrets in the diff, or without approval.
3. One logical change per commit — suggest a split if mixed.
4. Explain WHY, not just what; reference the context map.
5. Respect protected/irreversible files (backup ritual first).

Stop after presenting for approval. Commit only on explicit confirmation.
