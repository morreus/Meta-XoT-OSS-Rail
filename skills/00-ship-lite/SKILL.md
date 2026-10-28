---
name: 00-ship-lite
description: The short route for a small, low-risk change. Claude studies the project, plans and builds the change, and a second Claude reviews each step. There is no separate testing stage. If the change turns out to be risky, end the run and start /00-ship.
disable-model-invocation: true
argument-hint: <small change>
---

# 00-ship-lite — gated pipeline, short chain

**A run works only in Claude Code**, where the plugin's hooks guard it. If a pipeline command fails because
`pipeline.py` is not there, say in one line that a run needs Claude Code, and stop: do not carry out the run's
steps without the pipeline.

**Read the `00-ship` skill now and follow it exactly** — the scoring rule, the "you MUST use the
step skills" requirement, the commands, the three situations STEP 0 reads off the disk, the
override instructions and the completion protocol are all identical. Only these three things
differ:

1. **The chain is `lite`.** After STEP 0 — the look-before-you-ask opening in `00-ship`, which
   applies here unchanged, approval and all:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" init lite <start step> [<milestone>… | none]
   ```
   Inside the implementation branch — step 30 or after — the finished milestones are named, or
   `none`, the same rule as in `00-ship`.
2. **Six steps, target `6,5,4,3,2,1`:**
   `10-context-map · 11-review-map · 20-plan-impl · 21-review-plan · 30-implement-plan · 31-review-impl`
   The test steps (40/41/50/51) do not run. **Choosing lite is choosing to ship code that was
   reviewed but never tested** — run any quick existing tests as part of step 30's own
   verification, and say in the summary that no test step ran.
3. **Right-size guard — check once the map is written.** Lite is only for genuinely small, low-risk work.
   **If the map shows the change is bigger than expected, risky, or touches code that moves money,
   changes production data or cannot be undone, STOP and ask the operator to end this run (`question
   end`, then `/94-clean-process`) and start `/00-ship` (full) instead** — a second run cannot start
   while this one is live. Never use the lite chain on such code.

Everything else — the gate, the section checks, the `92-fix` loops, no push — is
exactly as `00-ship` describes.

## Suggested `/goal`
```
/goal Deliver «FEATURE» following the 00-ship-lite skill (which defers to the 00-ship skill) — read BOTH first. Step 1: do STEP 0 of 00-ship — brief me in the chat, then show me its sheet, and WAIT for my click (or my number, where no sheet can be shown). Step 2: on my click, do the setup STEP 0 gives for the option I chose — `init lite`, adopting what that option names, or `bind` if the run is live — exactly as the 00-ship skill spells the command (the skill carries the path; a pasted line cannot). Then repeatedly: run `status`, work ONLY the open ticket — you MUST invoke the `<id>-gated` skill and follow its method, and close the ticket the way that skill's tail says. DONE only when `pipeline.py status` says the chain is complete and you output a line starting SHIP-COMPLETE. If the pipeline holds the run on a question, show it to me once and WAIT in silence for my answer; then carry on to the target. Stop after 30 turns if blocked.
```
