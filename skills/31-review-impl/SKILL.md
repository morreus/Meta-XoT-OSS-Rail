---
name: 31-review-impl
description: A second Claude reviews the code that was just built, file by file, against the plan, the project's style and its history. It proves what the code does instead of trusting it, and rates each problem high, medium or low. Use it after /30-implement-plan, before /60-commit.
disable-model-invocation: true
argument-hint: <feature being implemented>
---

ultrathink: Adversarially review the implementation for: $ARGUMENTS — with your own receipts.

**Which file.** `<slug>` names the work: the context map document is the one `/10-context-map` wrote for it, and the results file carries the same slug. If `docs/` holds more than one context map document and neither the request nor the conversation says which, ask.

## Prerequisites
- A plan exists in `docs/context_map_<slug>.md` and there are changes to review — uncommitted, or committed
  since the previous milestone's commit.
- Read the plan (intended scope, milestones, assumptions) and `${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md` + `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md`.

## SCOPE — ONE milestone, and it is not the whole diff

`/30-implement-plan` implements **exactly one milestone**. This review covers **that milestone**,
and the plan names which one. If you were not told, ask before reviewing — do not guess, and do not
review everything you can see.

**In scope**
- The changes this milestone made, against **its own exit criteria** in the plan.
- **Regression** — did this milestone break something that previously worked? Trace the call sites
  of every changed symbol. This is not scope creep; it is the point.
- Side effects the milestone caused elsewhere, including files it did not mean to touch. (An import
  that silently rewrites a dependency manager is this milestone's problem, whoever typed it.)

**Out of scope — and this is a rule, not a preference**
- Other milestones' work, whether already done or not yet due.
- Pre-existing defects the milestone merely sits next to.
- The plan itself, and whether the milestone was the right idea.

**Out-of-scope findings are capped at Low.** However real they are, they cannot be High or Medium
*for this milestone*, because this milestone cannot discharge them — and a finding that cannot be
discharged blocks the stage forever. Record them plainly so they are not lost: **the finding text
begins with `OUT OF SCOPE:`**, as the map review's does, says which milestone or follow-up owns it,
and the severity reflects what THIS unit of work can answer for. The marker keeps them findable: a
`/00-ship` run lists them all at its end, so none is lost.

## What to review — the diff for THIS milestone
- **On the plan's highest-numbered milestone, when it has more than one besides M0, your job is the END-TO-END review**, and the
  absence of code there is not a finding: that milestone builds nothing by design,
  and this is the FIRST review of it — on the full chain four test
  steps follow. Review the run across everything the earlier
  milestones shipped, plus whole-feature regression; what breaks there is a finding, and the
  empty implementation is the design.
- **The milestone's change lives in the working tree** — a milestone is committed once its
  reviews are done, not before — so read it there, against `<commit>`: the previous milestone's
  commit (`git log --oneline -5` finds it), or on the first milestone the commit the work started
  from. Three things, and all three:
  - `git status --porcelain --untracked-files=all` — every changed and every new file;
  - `git diff <commit>` — the tracked changes, against the working tree;
  - **every new file, read in full** — a diff shows none of them.

  Not a range ending at `HEAD`, which is empty while the milestone is uncommitted, and not a bare
  `git diff`, which skips the new files.
  ⚠️ The working tree may contain **other milestones' work as well**. The plan's milestone
  section, and the file list `/30-implement-plan` recorded for it, are your boundary. State plainly
  in your verdict which files you treated as in scope and why.

**Do NOT review `HEAD~1`** unless it is the previous milestone's commit — otherwise that is history,
not your new work.

## Stance — CHALLENGE, don't rubber-stamp
Assume the diff has a bug until your own checks prove otherwise. Don't trust naming or comments — verify behaviour. Review the diff **file by file** (you lose focus reviewing a large diff all at once).

### Round 1 is a full pass. Round 2 and after are scoped.

If no review of THIS step on THIS unit of work has happened before, you are round 1: sweep
everything, and sweep it properly — every later round costs what this one saves.

If one has — a fix preceded you, and you were told so or the earlier findings are in front of
you — you are re-reviewing a FIX. Read, in this order:

1. the findings the fix claims to discharge;
2. the new facts the fix lists — every claim it wrote, and what it ran or opened to check each;
3. what changed, against the right point — **a fresh review: what changed since the last fresh
   review; a review of your own fix: what changed since the previous round.** Not only the round
   before: after a clean round of your own fix, that round already holds every fix of the loop,
   and a fresh look compared with it would see none of them;
4. **search for the old wording** of every line the change touched, across the whole artifact, and
   report every place it survives in one finding — a record of the repair, or a section the
   artifact keeps as superseded, is not a surviving copy. The same fact written in several places
   is the commonest thing a fix leaves behind, and this is the search that finds it;
5. those sections in full, re-derived from the code as always — plus anything the change could
   have broken.

You are NOT required to re-derive the whole artifact.

Two things this does not license. **A fix that rewrites the artifact rather than patching it is a
round 1 again** — say so and sweep it. And **scope is not leniency**: within what you read, the
burden of proof is unchanged, and if the fix's own claims do not survive checking, that is a
finding however small the diff was.

### Fresh eyes — and what to do when you can't have them
If you are reading this in your own agent, with none of the conversation that produced the work,
you ARE the fresh eyes and nothing needs arranging — skip to the rules below. **Otherwise there is
no separate agent reviewing and no fresh eyes to arrange.** Do NOT try to delegate this to a subagent: nothing checks
who reviewed what, so a delegated review buys you a claim nobody can verify and a failure mode
(denied tool, nesting limit, an agent that dies silently). Review it yourself, do not skip it, and
do not call it independent. Compensating rules:

1. **Re-derive, never re-read.** Answer each check from the *code and the repo*, not from the
   artifact's reasoning. If the artifact cites `file:line`, open it. If it claims a behaviour, run
   or trace it. Treat the artifact as a claim under test, not as context.
2. **Invert the burden of proof.** Your default verdict is "not proven". A point only clears when
   your own evidence clears it.
3. **Attack the parts you are most confident about** — self-review fails precisely where the author
   was sure, so spend the effort there rather than on the parts already flagged as uncertain.
4. **Say so plainly in your verdict**: this was a self-review without independent eyes, so it
   carries less weight than a fresh-eyes pass. Never describe it as independent — that word is
   reserved for a review by an agent that did not write the artifact.
5. If the change is high-risk (production, money, or anything that cannot be undone) and you could not get an
   independent review, **say so to the user and recommend a second pair of eyes before commit.**

### Severity — the one test, in the words both parties read
A finding is BLOCKING if, shipped as it stands, the system would do something wrong. A finding is LOW if it is true, worth recording, and changes nothing anyone does. A defect nothing can currently reach is LOW unless the change under review also supplies the path that reaches it. A finding about how a document reads — wording, a stale line number or cross-reference, a copy that disagrees without changing what gets built — is LOW; a document finding blocks only when someone building from it would do the wrong thing.
Every finding carries one of three words — HIGH, MEDIUM, LOW — and this is the only test that
decides which. Not how serious it feels, not how much work it is. Two reviewers may find different
things; they must not grade the same thing differently. **The one rule it works beside is scope,
above:** a finding outside what this review covers is LOW and its text begins with
`OUT OF SCOPE:`, because this
unit of work cannot discharge it — the test grades what this work can answer for.

---

## PHASE 1: Independent verification (don't just read the diff)
- **Codebase** — grep for the conventions/utilities this change should match or reuse; find call sites and callers of changed symbols; confirm nothing else depended on the old behaviour.
- **Prove behaviour** — trace the actual execution path for a concrete normal input AND a failing/edge input. Run the code/test where feasible and read the REAL output. Do NOT infer "it works" from good names.
- **Git** — `git log -S "<symbol>"` / `git blame` on the changed lines: was this tried/reverted before? Are you re-introducing a known bug?
- **Web** (only for bespoke / non-obvious code) — is the approach a known antipattern for this stack? Surface pitfalls.

---

## PHASE 2: Findings (tag every finding High / Medium / Low per _shared.md severity discipline)

1. **Does it deliver the request?** — read `## 0. The request` in the working document and ask
   whether this diff delivers *that*. Separate from plan adherence below: a diff can implement the
   plan exactly while the plan drifted from what the operator asked for. This is the only check in
   the chain that compares the finished work against the beginning, so do it properly — quote the
   request and say, point by point, what delivers it.
2. **Plan adherence** — all planned items done? Any unplanned scope added (should be removed or split out)?
3. **Correctness** — logic errors, wrong conditions, off-by-one; edge cases (empty/null/boundary); type/precision issues.
4. **New issues the diff surfaces** — race/timing, state-management gaps, API-contract violations, missing error handling.
5. **Convention consistency** — deviations from existing patterns (cite the existing pattern at file:line).
6. **Stack-specific risks** — pull from `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md` risk checklist + the context map's Project-Risk Touchpoints (e.g. dtype/precision, data leaking from the future in time-series work, serialization, UI/resolution, secrets). Only what actually applies.
7. **Overengineering** — is there a simpler pattern already in the codebase? Dead code introduced?

### Second pass (only if the above is clean)
If you found no High/Med, do ONE more focused pass strictly on **edge cases and error paths** — that's where surviving bugs hide.

## Where your review goes
The body of this review belongs **in the conversation**, where the operator reads it. Every
finding carries its **severity** and its **proposed fix**, and names where the fix goes — the
fixer works from these, and a finding without a proposed fix is one it has to rediscover. The
findings table below is the record.

### Findings
| # | Finding | Severity | Location (file:line) | Concrete failure it causes | Suggested fix |
|---|---------|----------|----------------------|----------------------------|---------------|

### Verdict
- [ ] ✅ Clean (no High/Med) — the next step opens
- [ ] 🔄 Fix required — [list the High/Med items]

A pass is clean only with no High and no Medium. Per the review loop in `_shared.md`: if there are High/Med findings, the fixes are applied via `/92-fix` and this review re-runs until clean.

Stop. Do not modify code here — you are reviewing; fixes are applied by `/92-fix` (or the producing skill), then a fresh re-review runs.
