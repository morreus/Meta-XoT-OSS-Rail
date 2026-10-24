---
name: 41-review-test-plan
description: Adversarial fresh-eyes review of the TEST PLAN — coverage, that the test-type checklist was truly walked, that acceptance criteria are measurable, and that no test is written so it cannot fail. Run after /40-test-plan. The results are reviewed by /51-review-tests.
disable-model-invocation: true
argument-hint: <feature>
---

ultrathink: Adversarially review the TEST PLAN for: $ARGUMENTS.

**Which file.** `<slug>` names the work: the context map document is the one `/10-context-map` wrote for it, and the results file carries the same slug. If `docs/` holds more than one context map document and neither the request nor the conversation says which, ask.

## Prerequisites & target
- [ ] `docs/context_map_<slug>.md` contains the test plan (from `/40-test-plan`).
- Read the test plan, the context map (Project-Risk Touchpoints), the actual diff, and `${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md` + `<stack>.md`.

## Stance — CHALLENGE, don't rubber-stamp
Assume the tests are weaker / less honest than they look until you've checked.


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

## On the highest-numbered milestone
That milestone builds nothing by design, and its test plan is the **release-level** suite across
everything the earlier milestones shipped. The absence of milestone code there is **not a
finding**; a plan that tests the whole feature end-to-end is the right plan, and one that tests
nothing because "there is no code" is the wrong one.

## Reviewing the test plan (tag findings High / Medium / Low)

**0. CAN IT RUN? Take every scenario's preconditions FIRST, before anything else.** For each one,
ask how that starting state is arranged — fixture, emulator, seeded instance, mock. If the answer
is "production will happen to be in this state", the scenario does not exist, however well it is
written, and that is a **High**. Judge it against reality, not the plan's own optimism: if the
precondition is an empty queue, is the live queue something the tester controls?

Do this before coverage, criteria or priorities. A plan can be immaculate on all of those and still
be unrunnable, and reviewing in the usual order finds the polish and misses the floor. Worse: an unarrangeable precondition
pressures whoever runs it to CREATE that state, and the states worth testing are the destructive
ones. A scenario that can only run by deleting real users' data is a High whatever else it gets
right.

1. **Coverage** — read the diff; does every changed code path/branch have a test? List uncovered paths.
2. **Test-type checklist actually walked** — was EACH of the test-type categories (happy/boundary/invalid/null/error-paths/idempotency/state/concurrency/scale/precision/time/external/security/regression + stack-specific) either turned into a scenario OR marked N/A with a real reason? **Any whole type silently skipped is a finding** — name the missing edge cases.
3. **Acceptance criteria** — measurable, pass/fail? Any subjective "works correctly" criterion is a finding.
4. **Too-easy tests / instruments that cannot fail** — for EVERY test and control ask: *what would
   this look like if the feature were absent?* If the answer is "the same", the test is worthless.
   Demand evidence of a mutation check (break it, watch it fail) for anything claimed as passing.
   Flag unconditional logging, controls that don't actually disable, and durations/counters that
   would read identically if the code never ran.
5. **Risk coverage** — is every Project-Risk Touchpoint mapped to a test? Do irreversible-action tests use dry-run/fixtures, never live?
6. **Priorities** — are the P0s actually the highest-impact scenarios?

## Where your review goes
The body of this review belongs **in the conversation**, where the operator reads it. Every
finding carries its **severity** and its **proposed fix**, and names where the fix goes — the
fixer works from these, and a finding without a proposed fix is one it has to rediscover. The
findings table below is the record.

### Findings
| # | Finding | Severity | Location (test id / file:line) | Concrete failure it causes | Suggested fix |
|---|---------|----------|--------------------------------|----------------------------|---------------|

### Verdict
- [ ] ✅ Sound, no High/Med findings — execute it (`/50-test-impl`)
- [ ] 🔄 Revise — add the missing coverage / test types / measurable criteria

A pass is clean only with no High and no Medium. Per the review loop in `_shared.md`: revise/fix via `/92-fix` and re-review until clean; **failing tests block commit**; if a High/Med can't be resolved, stop and warn the user.

Stop. Do not modify code or fabricate results.
