---
name: 30-implement-plan
description: Implement exactly one milestone from the plan, with self-verification, blocking on unknowns, and mandatory doc updates. Requires a plan first. Invoke explicitly after /20-plan-impl.
disable-model-invocation: true
argument-hint: <milestone id, e.g. M1 (optional)>
---

Implement milestone $ARGUMENTS from the plan in the working document, `docs/context_map_<slug>.md`.

If no argument is given: implement the next unfinished milestone.

---

**Which file.** `<slug>` names the work: the context map document is the one `/10-context-map` wrote for it, and the results file carries the same slug. If `docs/` holds more than one context map document and neither the request nor the conversation says which, ask.

## PHASE 0: Pre-flight Check (MANDATORY)

- [ ] `docs/context_map_<slug>.md` exists and holds the implementation plan. A context map is expected too,
      unless the plan has an *Agreed context* section — what was agreed in conversation, written down — in its place (work that began from an agreed plan) —
      do not stop and demand a map in that case.
- [ ] Target milestone is defined with clear exit criteria
- [ ] No unresolved blockers from previous milestones
- [ ] This is not the plan's **highest-numbered milestone**, when the plan has more than one besides M0. That one builds nothing by design
      and has no implementation to do, so if you were asked to implement it, the plan is wrong
      about it: STOP and say so.

**If any check fails → STOP. Run `/20-plan-impl` first.**

Required sections: none

The artifact of this step is the code — a working tree that changed since the previous
milestone's commit — not headings. Re-read the milestone NOW: files to change, verification steps, exit criteria, assumptions to validate. If stack rules aren't in context, read `${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md` + `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md`.

---

## PHASE 1: Implementation

### Rules — STRICTLY ENFORCE
1. **ONLY this milestone** — no scope creep, no "while I'm here" changes.
2. **No unrelated refactors** — note tech debt in `docs/context_map_<slug>.md`, under a *Future work* heading (add it if missing).
3. **Match existing patterns** — grep for similar code first, follow conventions.
4. **Minimal diff** — smallest change that achieves the milestone goal.
5. **Never perform an irreversible/production/money-touching action autonomously** — if the milestone touches anything in the context map's **Project-Risk Touchpoints** (e.g. payments, production data, the project's protected files), STOP and hand back to the user with exactly what you intend to do. Destructive git / `rm -rf` are confirmation-gated regardless.

### Blocked Check (before AND during implementation)
If you hit: unclear requirements, missing information, unexpected behavior, or an assumption proven wrong → **STOP**.

When blocked:
1. Document the blocker in `docs/context_map_<slug>.md` → Unknowns.
2. Describe what you learned and how to unblock.
3. **Ask the user** the specific question — do NOT assume an answer to keep moving.
4. Output: `BLOCKED: [reason]`. Do not fabricate success or work around it.

### Instrumentation (only if needed to verify)
Add debug logging when the milestone can't be verified confidently or an assumption needs runtime validation. Use **the stack's instrumentation style from `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md`**:
- Python: `logging` gated by a `--debug` flag/env — not bare `print()` spam.
- Unity: `Debug.Log` under `#if UNITY_EDITOR || DEVELOPMENT_BUILD`.
- Flutter: `debugPrint` / `assert` under `kDebugMode`.
Low-noise, event-based. Mark it clearly removable; gate or remove before commit.

---

## PHASE 2: Self-Verification (MANDATORY)

### Code Verification
- [ ] Compiles / imports cleanly; no new warnings
- [ ] Linting/formatting passes (if the project uses it)

### Behavior Verification
Run the verification steps from the plan and record ACTUAL results:
| Step | Expected | Actual | Pass? |
|------|----------|--------|-------|
| ... | ... | ... | ✓/✗ |

### Cross-Reference Check
- [ ] Implementation matches the plan spec
- [ ] All planned files changed (no more, no less)
- [ ] Exit criteria met

### Self-review of your own diff
- Re-read your diff **file by file** (don't eyeball the whole thing at once — you lose focus on large changes).
- **Prove behaviour, don't infer it from names**: run the code / test and paste REAL output; don't assume a function works because it's named well.
- **Second pass on edge cases & error paths**: once the happy path passes, deliberately re-check empty/null/boundary inputs and failure handling — that's where the bugs hide.

**If ANY verification fails → fix it, or mark the milestone INCOMPLETE with the reason.**

---

## PHASE 3: Documentation Update (MANDATORY)

Update `docs/context_map_<slug>.md` — write into it, and never open it by overwriting:
- **Milestone status:** ✅ DONE / ❌ INCOMPLETE / 🚧 BLOCKED + timestamp + commit hash (if committed) —
  **written under the milestone's own existing heading, never as a new `M<n>` heading.** Every
  `#### M<n>` heading is a milestone, and a second heading for the same number makes its section
  undecidable: *one milestone, one heading*. A status line, a `Log` sub-section, a table row —
  anything but a heading whose first word is the milestone's id.
- **Files this milestone touched** — the explicit list, with what changed in each. ⚠️ **This is the
  reviewer's scope boundary, so it is not optional.** Until earlier milestones are committed, a
  reviewer running `git diff` sees every milestone's work at once and cannot tell yours apart; this
  list is the only thing that separates them. Include files you touched *accidentally* — an SDK
  import that rewrites a dependency manager belongs here even though you did not type it.
- **Instrumentation added:** what it logs, how to trigger, where output appears, how to remove.
- **Discoveries:** anything learned that affects later milestones; assumptions validated/invalidated.
- **Assumptions Ledger:** update validated/invalidated entries.

---

## PHASE 4: Output Summary

**Files Changed:**
| File | Change Type | Lines |
|------|-------------|-------|

**Remaining Assumptions:** | # | Assumption | Status (Validated ✓ / Pending / Invalidated ✗) |

**Verification performed** — per the stack's verification style (from `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md`), e.g.:
- Python: ran the script / `pytest`; pasted real output; sanity-checked data (row counts, dtypes).
- Unity: entered Play mode; tested at ≥ 2 aspect ratios (e.g. 16:9 and 9:16); captured Console/screenshot.
- Flutter: `flutter test` + `flutter analyze`; ran on a device at ≥ 2 screen sizes.

**Milestone Status:** ✅ COMPLETE / ❌ INCOMPLETE [what's left] / 🚧 BLOCKED [blocker + how to unblock].

---

## CRITICAL RULES — DO NOT VIOLATE
1. **Never fabricate success** — if verification fails, say so.
2. **Never skip verification** — run the actual steps, report actual results.
3. **Stop when blocked; ask, don't assume** — never work around an unknown.
4. **One milestone only** — resist "one more thing".
5. **Never perform irreversible/production/money-touching actions autonomously** — hand back to the user.
6. **Code changed = docs updated** — no exceptions.

Stop after Phase 4. Do not proceed to the next milestone without user approval.
