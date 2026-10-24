---
name: 51-review-tests
description: Adversarial fresh-eyes review of the TEST RESULTS — hunts false positives, tests that cannot fail, fabricated evidence, and skipped P0s. A green check that is wrong is the worst outcome the process can produce. Run after /50-test-impl.
disable-model-invocation: true
argument-hint: <feature>
---

ultrathink: Adversarially review the TEST RESULTS for: $ARGUMENTS.

**Which file.** `<slug>` names the work: the context map document is the one `/10-context-map` wrote for it, and the results file carries the same slug. If `docs/` holds more than one context map document and neither the request nor the conversation says which, ask.

## Prerequisites & target
- [ ] `docs/test_results_<slug>.md` exists (from `/50-test-impl`), and `docs/context_map_<slug>.md`
      contains the test plan those results answer.
- Read the test plan (and results), the context map (Project-Risk Touchpoints), the actual diff, and `${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md` + `<stack>.md`.

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
That milestone builds nothing by design; the results under review are the **release-level**
suite's, run across everything the earlier milestones shipped. The absence of milestone code
there is **not a finding**; results that never exercised the whole feature end-to-end are.

## Reviewing the test results (tag findings High / Medium / Low)
1. **No false positives / no lies — do this thoroughly. A green check that's wrong is the worst outcome.**
   - **Re-run independently:** re-execute EVERY P0 test and a sample of the rest yourself (where safe), and compare to the claimed verdict. If your result differs, the claimed PASS is a **false positive → High**.
   - **Would it fail if the feature were broken?** For each PASS, confirm the test actually depends on the real output and *would* fail if the behaviour were wrong. A test that cannot fail (tautology, no-op, asserts nothing meaningful, passes on empty input) is worthless → **High**.
   - **Real evidence:** the recorded "actual" must be genuine captured output — not the expected value copied in, not fabricated, and internally consistent/plausible.
   - **Lie smells:** steps claimed done but skipped; "it didn't crash" reported as PASS; evidence missing; only the happy path exercised. Any of these → the PASS is not trustworthy.
   - If you cannot independently confirm a PASS, **downgrade it to SUSPICIOUS** — never accept an unverified PASS.
2. **Uncertainty handled** — are SUSPICIOUS/INCONCLUSIVE results marked as such, not buried inside PASS?
3. **Failures** — every FAIL/SUSPICIOUS is a real issue and a **High** finding that blocks `/60-commit`. No failing test glossed over or skipped to keep moving.
4. **Executed coverage** — were P0/P1 actually run (not skipped without a real reason)? **Check the
   results account for every test ID in the plan** — a summary line like "P0: N/N PASS" is not
   evidence that all N exist in the document. Any plan ID absent from the results is a High.
5. **Stale-run check** — did the reported run include the fixes? Compare the test count against the
   plan; an unchanged count after tests were added means a stale binary was measured.
6. **Evidence quality** — real actual output, not the expected result copied in as "actual".
7. **Integrity** — is the per-test integrity self-check present and honest?

---

## Where your review goes
The body of this review belongs **in the conversation**, where the operator reads it. Every
finding carries its **severity** and its **proposed fix**, and names where the fix goes — the
fixer works from these, and a finding without a proposed fix is one it has to rediscover. The
findings table below is the record.

### Findings
| # | Finding | Severity | Location (test id / file:line) | Concrete failure it causes | Suggested fix |
|---|---------|----------|--------------------------------|----------------------------|---------------|

### Verdict
- [ ] ✅ Trustworthy and green, no High/Med findings — proceed to `/60-commit`
- [ ] ❌ Failures or gaps — fix and re-test. **This blocks commit.**

A pass is clean only with no High and no Medium. Per the review loop in `_shared.md`: revise/fix via `/92-fix` and re-review until clean; **failing tests block commit**; if a High/Med can't be resolved, stop and warn the user.

Stop. Do not modify code or fabricate results.
