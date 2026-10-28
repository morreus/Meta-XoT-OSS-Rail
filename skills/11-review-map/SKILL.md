---
name: 11-review-map
description: A second Claude reviews the study written by /10-context-map. It re-checks the code, the git history and the web, questions every claim, and lists gaps and open questions. Use it before planning.
disable-model-invocation: true
argument-hint: <feature being mapped>
---

ultrathink: Adversarially review and challenge the context map for: $ARGUMENTS — with your own receipts.

**Which file.** `<slug>` names the work: the context map document is the one `/10-context-map` wrote for it, and the results file carries the same slug. If `docs/` holds more than one context map document and neither the request nor the conversation says which, ask.

## Prerequisites
- [ ] `docs/context_map_<slug>.md` exists (from `/10-context-map`).

**If missing → STOP. Run `/10-context-map $ARGUMENTS` first.**

Read the entire context map NOW, plus `${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md` + `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md` and the project `CLAUDE.md`.

**Scope:** the context map ONLY (evidence stage, before any plan). If a plan/milestone section already exists, ignore it — that is `/21-review-plan`'s job. You are not proposing the solution here.

### The request sets what is in scope
The map's `## 0. The request` records what was asked, in the requester's words. Review the map
against THAT:

- **A finding about something the request did not ask for is LOW**, however real it is — and it is
  still recorded, so it is not lost: its finding text begins with `OUT OF SCOPE:` and says where it
  belongs.
- **When the request is a goal and a list, the list sets the scope.** An item that is not on the
  list is out of scope, even when it would serve the goal.
- **What this does not cover:** a gap or an error in the map that would make someone build the
  requested work wrong is in scope, wherever in the codebase it sits — grade it by the test below.

### The map's own design is LOW; what the operator decides from is not
The map describes the code as it is; the plan designs the new code. So:

- **Design the map writes as its own** — the new code's flow, its stages, its checks, its schemas, or
  an assumption about how the new code will behave —
  **is one LOW**, never a MEDIUM or HIGH on that ground, and its finding text says *not settled; the
  plan decides it*. The plan review grades that design where the plan makes it.
- **An option or recommendation the map puts to the operator, and every fact it rests on, is graded
  by the test below**, because they decide from it: a false fact under an option they are asked to
  choose blocks like any other.
- **A false statement about the code as it is stays graded by the test wherever it sits** — design
  text around it does not make it LOW.

## Stance — CHALLENGE, don't rubber-stamp
Assume the map is optimistic and incomplete until your own evidence proves otherwise. Your job is to find what's missing, wrong, or unverified. Do NOT take the map's word for anything — re-derive it.

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
things; they must not grade the same thing differently. **The two rules it works beside are
above:** a finding outside what this review covers is LOW and its text begins with
`OUT OF SCOPE:`, because this
unit of work cannot discharge it — the test grades what this work can answer for; and design the map
writes as its own is one LOW, *not settled; the plan decides it*.

---

## PHASE 1: Independent investigation (do your OWN digging — not just read the map's receipts)

### Codebase (independent)
- Glob/Grep the repo yourself for the feature's symbols, entry points, callers, and related modules. Build your own picture, then diff it against the map.
- Open the map's cited files **and** their neighbours/callers. Confirm each claim says what the map says; find coupling or call sites the map omitted.

### Git (independent)
- `git log -S "<symbol>"`, `git log --grep="<term>"`, `git blame` on key files. Was this built/attempted/reverted before? Did the map miss relevant history?

### Web (independent)
- Search "[detected stack] + [the problem/approach] + known issues OR best practices". Confirm or **refute** the map's web findings; surface pitfalls, version gotchas, or established patterns it missed.

---

## PHASE 2: Challenge (tag every finding High / Medium / Low per _shared.md)

1. **Evidence quality** — unsupported, mis-cited, or stale claims you found while spot-checking. "No repo evidence" where that's the honest state.
2. **Coverage / correctness** — entry points, data/state flow, files/symbols, stack-specific specifics: what did your Phase 1 dig surface that the map missed or got wrong?
3. **Prior art** — existing patterns/solutions the map should reuse but didn't find.
4. **Unknowns & assumptions — honesty** — anything marked UNKNOWN that's actually discoverable (lazy unknown); confidence levels not justified by evidence; Low/Med-confidence items that can't be validated and must become **questions** when they are about what the work should do — a technical one is settled by a check in the plan, not a question — not silent assumptions.
5. **Project-risk touchpoints** — CLAUDE.md / stack invariants, secrets, or irreversible/production operations this change touches that the map failed to surface.
6. **The map's clarifying questions** — are they the right ones (only what's truly unanswerable from evidence)? Any that ARE answerable from the repo and should be removed and answered now? If the work needs a stack the project does not have and none was given: was it asked last, on its own, with three options (or fewer, merged as §9 allows), each price with its source?
7. **Questions YOU would add** — your own list of what must be answered before planning can start. Be specific.

## Where your review goes
The body of this review belongs **in the conversation**, where the operator reads it. Every
finding carries its **severity** and its **proposed fix**, and names where the fix goes — the
fixer works from these, and a finding without a proposed fix is one it has to rediscover. The
findings table below is the record.

### Findings
| # | Finding | Severity | Your evidence (file:line / commit / URL) | Suggested fix |
|---|---------|----------|-------------------------------------------|---------------|

### Verdict
- [ ] ✅ Map is sound (no High/Med findings) — proceed to `/20-plan-impl`
- [ ] 🔄 Needs revision — [specific changes]
- [ ] ⛔ Needs more evidence — [what to investigate]

A pass is **clean** only with no High and no Medium findings.

Stop. Do not write a plan or implement anything.
