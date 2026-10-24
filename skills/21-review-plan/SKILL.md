---
name: 21-review-plan
description: Adversarial fresh-eyes review of the implementation PLAN — challenges the chosen approach, validates options/assumptions against codebase+git+web, checks milestones, risks, and overengineering. Run after /20-plan-impl, before implementing.
disable-model-invocation: true
argument-hint: <feature being planned>
---

ultrathink: Adversarially review and challenge the implementation plan for: $ARGUMENTS — with your own receipts.

**Which file.** `<slug>` names the work: the context map document is the one `/10-context-map` wrote for it, and the results file carries the same slug. If `docs/` holds more than one context map document and neither the request nor the conversation says which, ask.

## Prerequisites
- [ ] `docs/context_map_<slug>.md` exists **AND contains the implementation plan** (from
      `/20-plan-impl`). The file existing is not enough — check the plan is actually in it.
      A context map is expected too, unless the work began from an agreed plan with no map; then the plan's
      *Agreed context* section — what was agreed in conversation, written down — stands in for it.

**If the plan is missing → STOP. Run `/20-plan-impl $ARGUMENTS` first.**

Read the whole doc NOW (context map + plan), plus `${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md` + `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md` and `CLAUDE.md`.

**Scope:** the PLAN (and whether it's consistent with the already-reviewed context map). You're not re-grading the map's evidence unless the plan exposes a gap in it.

## Stance — CHALLENGE
Assume the recommended approach is not yet the best or safest option until evidence proves it. Try to find the better/simpler/safer path the plan missed.

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
things; they must not grade the same thing differently.

---

## PHASE 1: Independent validation (don't just trust the plan)
- **Codebase** — does the prior art the plan cites actually exist and fit? Grep for the patterns/utilities yourself; is there a simpler existing approach the plan ignored? Open the files it lists and sanity-check the "~N files changed" estimates.
- **Git** — `git log -S`/`blame`: was a similar approach tried and reverted? Does history argue against this?
- **Web** (bespoke/non-obvious approaches only) — known antipattern? pitfalls the plan didn't mention?

---

## PHASE 2: Challenge (tag every finding High / Medium / Low per _shared.md severity discipline)

1. **Does it deliver the request?** — read `## 0. The request` in the working document, in the
   operator's own words, and ask whether this plan actually delivers *that*. This is a different
   question from whether the plan matches the map: the map can be perfect and the plan can still
   have drifted from what was asked. Anything the request asked for that the plan does not cover,
   and anything the plan adds that the request never implied, is a finding.
2. **Approach validation** — is the recommended option justified over the alternatives by **evidence, not preference**? Were alternatives fairly evaluated? Does it match existing codebase patterns? Is each option grounded in a concrete pattern (file:line) or just generic prose?
3. **Plan gaps** — missing requirements, unclear steps, unaddressed dependencies; missing edge cases (cross-check against the test-type categories: boundary, null/empty, error paths, concurrency, idempotency, precision, time…).
4. **Assumptions** — are Low/Med-confidence assumptions handled (M0 / validation, or surfaced as a question)? Any silent assumption that should be a question? Any assumption that's actually checkable now — and wrong?
5. **Pre-mortem quality** — did the plan genuinely pre-mortem the chosen option? Add failure modes it missed.
6. **Milestone structure** — M0 present if Low/Med assumptions exist, and **absent as a heading if not** (every `#### M<n>` heading is a milestone that is implemented on its own; a heading that says "not applicable" is a milestone nothing can finish — MEDIUM); M1 truly minimal (<5 min, 1–2 files); milestones sequential with clear exit criteria; each names how it's tested; with more than one shipping milestone (any but M0), the **highest-numbered** one is the integration milestone and **builds nothing** — anything that builds sits before it. **Is each step correct against the context map and the actual codebase? (highest importance).**
7. **Scale, edge cases & risk** — pulled from the stack risk checklist + Project-Risk Touchpoints; anything missing? Are irreversible/production steps flagged and gated?
8. **Overengineering** — is there a simpler viable path? YAGNI violations? Is new architecture actually needed? What can be removed now?

### Second pass (only if the above is clean)
Take the single riskiest milestone and ask: what's the one thing most likely to go wrong here, and does the plan cover it?

## Where your review goes
The body of this review belongs **in the conversation**, where the operator reads it. Every
finding carries its **severity** and its **proposed fix**, and names where the fix goes — the
fixer works from these, and a finding without a proposed fix is one it has to rediscover. The
findings table below is the record.

### Findings
| # | Finding | Severity | Evidence (file:line / commit / URL) | Concrete failure it causes | Suggested fix |
|---|---------|----------|-------------------------------------|----------------------------|---------------|

### Verdict
- [ ] ✅ Ready to implement (no High/Med findings) — proceed to `/30-implement-plan`
- [ ] 🔄 Needs revision — [specific changes]
- [ ] ⛔ Needs more evidence — [what to investigate]
- [ ] 🚫 Reconsider approach — [the fundamental issue]

A pass is clean only with no High and no Medium. Per the review loop in `_shared.md`: if there are High/Med findings the plan is revised via `/92-fix` and this review re-runs until clean; if a High/Med can't be resolved, stop and warn the user.

Stop. Do not implement anything.
