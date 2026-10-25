---
name: 20-plan-impl
description: Create an evidence-based implementation plan with validated assumptions, options analysis, and milestones. Requires a context map first. Invoke explicitly after /10-context-map.
disable-model-invocation: true
argument-hint: <feature or area to plan>
---

ultrathink: Create an implementation plan for: $ARGUMENTS

---

**Which file.** `<slug>` names the work: the context map document is the one `/10-context-map` wrote for it, and the results file carries the same slug. If `docs/` holds more than one context map document and neither the request nor the conversation says which, ask.

## PREREQUISITES CHECK

**REQUIRED**: the working document, `docs/context_map_<slug>.md`, holding the context map.
- If it is missing or has no map: STOP. Run `/10-context-map $ARGUMENTS` first.
- If present: read it NOW. It records the detected **stack**, the **Project-Risk Touchpoints**, and the unknowns/assumptions — reference them throughout.
- When the run starts here, the work needs a stack the project does not have, and neither the agreed context nor the request names it, ask it before planning, in the form `10-context-map` §9 describes.

If the stack rules aren't already in context, read `${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md` and `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md` (stack from the context map).

---

## PHASE 1: Evidence Validation (MANDATORY)

Before proposing ANY solution, validate against evidence:

### Codebase Check
- Search for similar patterns already in use; find prior art for this problem type
- Check conventions in related files; identify reusable utilities/components

### Git Archaeology
- `git log -S "relevant_term"` — has this been attempted before?
- `git log --oneline -- <affected files>` — recent changes that matter
- Check for reverted attempts or refactored patterns

### Web Research
For each candidate approach:
- Search: "[detected stack/language/framework] + [approach] + [best practices OR pitfalls]"
- Find established patterns vs. custom solutions; note known issues

---

## PHASE 2: The plan

**Write it INTO the working document**, below the map. The map and the plan are one document:
the plan is what the evidence in the map led to. Add your sections, and never open the file by
overwriting.

Required sections: Milestones · Acceptance rules · What could go wrong

Those three headings, exactly, are required, and inside a run they are checked for. Write them as headings. The
numbered sections are the method; §1–§4 come first as the evidence, then the three required
sections.

### 1. Repro Steps (if bug fix)
Exact steps; Expected vs Actual.

### 2. Evidence Summary
| Source | Finding | Implication |
|--------|---------|-------------|
| `path/file:L42` | Existing pattern for X | Reuse / Adapt |
| Git commit `abc123` | Previous attempt at Y | Learn from / Avoid |
| [Web source] | Known issue with Z | Mitigate |

### 3. Assumptions Ledger
| # | Assumption | Confidence | Validation Method | Validated? |
|---|------------|------------|-------------------|------------|
| A1 | ... | High/Med/Low | How to verify | ✓/✗/Pending |

**Rules:**
- Low/Medium confidence = MUST validate before or during implementation.
- If an assumption **cannot be validated from evidence**, do NOT silently assume it — surface it as a question to the user (per the "ask, don't assume" rule in _shared.md) — unless it is technical: then a check in M0 or the first milestone settles it, not a question.
- If any assumption is Low or Medium confidence, or the stack is new → M0 is required.

### 4. Options Analysis
For each (A: primary, B: alternative, C: simplest viable):
- Approach / Evidence ([codebase/git/web]) / Pros / Cons / Files changed (~N) / Risk (Low/Med/High)
- **Ground each option in a concrete codebase pattern (file:line) the project already uses** — not generic best-practice prose. Generic context produces solutions that don't fit this repo.

**Recommendation:** Option [X] because [evidence-based reasoning].

## Acceptance rules
What the finished work must satisfy, written before it is built — each rule checkable, each one
the thing a reviewer will hold the implementation to. Include the overengineering guardrails the
chosen option is held to:
- [ ] Simplest solution that works?
- [ ] Adding abstraction that wasn't requested?
- [ ] Does the codebase already have a pattern to follow?
- [ ] Can I modify existing code vs. new files?
- [ ] Solving future problems that may never exist?

Constraints: prefer modifying existing files; no new architecture/frameworks unless required; no premature generalization; match existing style.

## Milestones

Number them, and never reuse a number. **Every `#### M<n>` heading IS a milestone** — it is
counted, it is implemented on its own, and its implementation can only be accepted on code that
changed. So write a heading only for a milestone that builds something (or for the final
integration one). **If M0 is not needed, write no M0 heading**: say so in one sentence under this
section instead. A heading kept to explain why a milestone is absent is a milestone nothing can
finish. Each milestone is carried through the whole chain on its own —
implemented, reviewed, test-planned, that plan reviewed, tested, results reviewed — before the
next one starts. Per-milestone testing is what stops a shipment reaching production with its
acceptance test still unwritten.

#### M0: Set-up and instrumentation (when the stack is new, or Low/Med confidence assumptions exist — otherwise no M0 heading at all)
**When the stack is new** — chosen in the map, not yet in the project — M0 sets it up first: everything the stack
needs, downloaded and installed; the empty project created; the services connected (database, hosting, payments).
**Before installing anything outside the project, show the user the full list — each tool, what it is for, where it
goes — and wait for one approval of the whole list.** What only the user can do — create an account, pay a fee,
copy a key — is asked as an action question, with everything needed to do it in the chat. **Exit of the set-up:** an
empty app builds and runs where it will be used (the device, or the browser). Then M0 checks the plan's uncertain
assumptions on that running base, as below.
**Purpose:** Validate assumptions before committing to an approach.
**Scope:** targeted debug logging at specific locations, using **the stack's instrumentation style from `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md`** (e.g. Python `logging` gated by a `--debug` flag; Unity `Debug.Log` under `#if UNITY_EDITOR || DEVELOPMENT_BUILD`; Flutter `debugPrint` under `kDebugMode`). Low-noise, event-based.
**Verification:** trigger the action; observe output; confirm/reject assumptions.
**Exit:** assumptions validated, approach confirmed.

#### M1: Minimal Viable Change
Smallest change that proves the approach. Touch 1-2 files; single responsibility; verifiable in < 5 min.
| File | Change | Why |
|------|--------|-----|
**Verification:** per the stack's verification style (run the script / test / Editor play, as defined in stack rules). **Exit:** specific measurable outcome.

#### M2: Core Implementation
Main functionality. Scope / Changes / Verification / Exit.

#### M3: Polish & Edge Cases
Handle the cases from *What could go wrong*. Scope / Changes / Verification / Exit.

#### THE FINAL INTEGRATION MILESTONE — required when the plan has more than one shipping milestone (any milestone but M0)

Per-milestone testing cannot, by construction, catch a defect that only appears **between**
milestones, so a plan with two or more shipping milestones needs one more, and it is **the
highest-numbered milestone in the plan**. It is identified by its number, not by its position in
the text or by any flag, and it is treated differently: **it has no implementation of its own to
build, and nothing is built for it** — this milestone **builds nothing**. Anything that builds
goes in a milestone before it.
Integration fixes land in the repair rounds that follow its end-to-end review, which is where
they belong.

> **M<highest>: integration and release verification.**
> **Builds:** nothing — say so plainly, that is the design and not a gap.
> **Verification:** the end-to-end run across everything the earlier milestones shipped, plus
> whatever regression the whole feature needs. Its test plan is the release-level suite — the one
> with the cross-cutting coverage matrix that no single milestone's plan can hold.
> **Exit:** the feature works as a whole, not just milestone by milestone.

⚠️ **A defect found there does NOT automatically reopen the milestone that caused it.** Judge it:
- **A bug** — the milestone did what it set out to do and there is a defect in it → it is fixed
  in the repair round after the review that found it, recording which milestone's code changed.
  That round's own re-review covers the change. This is how release-candidate defects work
  everywhere else; you do not reopen the finished milestone.
- **A design defect** — the milestone's approach was wrong, or its exit criteria were never really
  met → the review that finds it **orders a rollback** to the document that was wrong, and
  everything built on that document loses its credit. Pretending otherwise would let the
  integration milestone become the place everything is quietly fixed while the closed
  milestones' reviews stop meaning anything.

## What could go wrong

**Pre-mortem (recommended option):** assume it shipped and broke. List the top 3 ways it failed (correctness, integration, scale, the project's risk touchpoints) and how the plan prevents each. If you can't prevent one, that's a question (when it is about what the work should do) or a new milestone.

**Scale & edge cases** — populate from this project's risk surface — **the stack risk checklist in `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md`** plus the context map's **Project-Risk Touchpoints** — not a fixed list:
| Risk (from stack rules / context map) | Consideration | How Addressed |
|---------------------------------------|---------------|---------------|
| ... | ... | ... |
Always include: empty/null input, boundary values, concurrent access, failure/rollback.

**Rollback plan** — record exactly how to undo this plan's changes: the branch or commit to return to, files to revert, and any data/migration to back out. For repos with irreversible or production/money-touching state (see the context map's Project-Risk Touchpoints), note the **backup/restore ritual required before any change** and that destructive git operations are confirmation-gated.

---

## RULES
1. **No guessing** — every claim needs evidence from codebase, git, or web.
2. **Ask, don't assume** — anything you cannot validate becomes a question when it is about what the work should do; a technical one becomes a check in M0, not a question.
3. **M0 is mandatory** if any assumption is Low/Medium confidence, or the stack is new.
4. **M1 must be tiny** — verifiable in < 5 minutes, minimal files.
5. **Simplest solution wins** — justify any complexity.
6. **Match existing patterns** — don't invent new conventions.
7. **Severity** — flag plan risks as High/Med/Low per _shared.md; High/Med must be addressed in the plan.
8. **Each milestone names how it will be tested** — verification is part of the plan, not an afterthought.

**Self-critique before finalizing:** would a skeptical senior engineer accept this plan? Is the recommended option justified over the alternatives by *evidence*, not preference? Is anything here generic rather than grounded in this codebase? Fix or flag.

---

