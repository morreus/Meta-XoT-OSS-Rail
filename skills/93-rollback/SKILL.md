---
name: 93-rollback
description: Used only inside a /00-ship run. When a review finds that later work followed an earlier document faithfully but that document was wrong, it reworks that document, or the current milestone's code before delivery. Delivered work is never touched.
disable-model-invocation: true
argument-hint: <the step number to rework — 10, 20, 30 or 40>
---

Rework: $ARGUMENTS

A review found something the step it was reviewing did **not** get wrong. The work was faithful; the
thing it was working *from* is wrong. So the repair belongs upstream, and this is it.

**You are not fixing the step that was reviewed.** That would be `/92-fix`. You are reworking an
earlier document so that everything built from it can be re-checked against a version that is right.

**This ticket is the exact counterpart of `/92-fix`.** When a review finds faults in the step it is
reviewing, a `92-fix` ticket opens on that step — not a second ticket for the step itself. When a
review orders a rollback, a `93-rollback` ticket opens on the earlier step, and again not a second
ticket for that step. Both are repair tickets scoped to a step; neither is a step in the chain, and
neither EARNS credit of its own. **The step you are repairing keeps the credit it already had** —
a repair does not withdraw it. (The OPENING of this ticket is what withdraws the
credit of the work built on the document, rather than the review's verdict or the operator's
instruction: an order that is refused must move nothing, and only the act tells them apart.) What lost its credit is everything built *on* the document you are about to
change, and that work is re-checked after you.

---

## Before anything: is this actually a rollback?

**Read the findings and the proposed fixes FIRST — they are in the ISSUES FILE**, `.metaxotrail/issues.jsonl`
in the project, one JSON entry per finding, each carrying the ticket it was raised under. Read every entry for the ticket that ordered
this rework before you touch the document — all of them, including the ones you think you can guess. You are executing a repair someone else diagnosed, not re-diagnosing it.

**You do not judge the findings.** Not whether the rollback was warranted, not whether the reviewed
step was really faithful, not whether a finding is worth acting on. That decision was made by the
review that opened this ticket and it is not yours to revisit — **the same rule `/92-fix` works
under.** Discharge what you can, **record plainly what you could not — in your own line's counts and
note, not in the issues file, which you cannot write** — and let the next review decide
whether anything still stands. A repair ticket that can talk itself out of the repair is a way past
a review.

**If a finding genuinely cannot be acted on** — it names no claim, no boundary, no assumption, so
there is nothing to rework — **raise a `question` and wait.** That is the mechanism; do not simply
stop, because the gate will not let the turn end and you will have named no legal next move. Expect
this to be rare: findings arrive with their proposed fixes attached, and one that cannot say what
is wrong is one the review should not have closed on.

*(You do not need to check that the target is legal. An unreachable or illegal `ROLLBACK` never
reaches this skill — the pipeline holds the ticket open and asks the operator instead of opening
it, or, where the ordering step reaches no target at all, refuses the close outright so the
reviewer writes a fix instead. A hold with nothing to offer is a door with no
exit.)*

---

## What can be rolled back to, and what cannot

**Only a document that later work is DERIVED FROM.** Four of them:

| Target | Why it is one | What derives from it |
|---|---|---|
| `10-context-map` | the plan reads the system through it | the plan, and everything after |
| `20-plan-impl` | the code, the tests and their plans are all built to it | the code, the test plan, the test run |
| `30-implement-plan` | the current milestone's code, until that milestone is delivered | that milestone's code review, test plan and test run |
| `40-test-plan` | the run executes it | the test run |

**`50-test-impl` is never a rollback target, and neither is a delivered milestone's code — this is
the important rule.** A test run is the thing under examination, not an input anyone derives from.

- **Wrong code found by its own review is fixed, not rolled back.** `/92-fix` on the
  implementation step. Wrong code found later — by the review of the test plan or of the test run —
  comes back here as `93-rollback:30`, while its milestone is not yet delivered.
- **A delivered milestone's work cannot be reverted.** The code is already in the repository. There
  is no "un-shipping" it; the only honest way to undo shipped work is **a new milestone whose job is
  to undo it**, planned and reviewed like any other. That is why milestone numbers are issued once
  and never reused.
- **A wrong test run is re-run.** Nothing derives from a record of what happened.

### Which reviews may order which

A review may reach back to any qualifying document **before its own pair** — never to its own
producing step, because "the thing I am reviewing is wrong" is a fix, not a rollback.

| Review | May roll back to |
|---|---|
| `11-review-map` | **nothing** — it is the first document; there is nothing behind it |
| `21-review-plan` | `10` |
| `31-review-impl` | `20`, `10` |
| `41-review-test-plan` | `30`, `20`, `10` |
| `51-review-tests` | `40`, `30`, `20`, `10` |

**Depth is legal but must be earned.** A jump from `51-review-tests` back to `10-context-map` is
rare and real — running the tests can be the first moment anyone notices the map named the wrong
entry point. It is not forbidden, because a repair path that cannot fire is the same as not having
one. But the deeper the jump, the more of the run it re-opens, so the reviewer's finding must name
the claim in that document which is wrong, not merely gesture at it.

---

## Reworking the PLAN — the milestone partition

This is the case with real machinery. The others are ordinary rewrites.

**Whichever document you rework, write INTO it and never rewrite its header.** The working document
carries the run hash the pipeline put there at `init`, and the next produce close reads it. Open
the file by overwriting it and the refusal lands two or three steps later, on an agent that did
nothing wrong.

### 1. Split the milestones

Read the plan and divide every milestone into two lists, **as they stood before the change that
triggered this**:

- **DELIVERED** — implemented, reviewed, tested, and their results reviewed. Credited.
- **NOT DELIVERED** — anything else, including one that is half-built.

Write both lists into the plan explicitly. The next reviewer checks them.

### 2. Delivered milestones are immutable

**You may not change a delivered milestone.** Not its text, not its number, not its position, not
its acceptance criteria. Not to tidy it, not to renumber around a gap, not to fold two together.
Their sections must come out of this rework **byte for byte** as they went in — each is hashed when
it earns credit, and this rework's close is refused if one has moved.

**If delivered work needs to change, that is a NEW milestone**, numbered next in sequence, describing
the change as work to be done — including work that undoes something. You do not edit history; you
add to it.

### 3. Undelivered milestones are fully open

Rewrite, merge, split, drop or reorder them as the reviewer's findings require. **Numbers for
anything new: the pipeline gives you the next free number with this ticket. Use that number and
count up from it — no other.** You cannot compute it yourself: the plan in front of you cannot show
a number dropped by an *earlier* rework, and the rule is never to reuse one, even one you just
dropped. Credit is stored against the number, and a recycled number attaches credit to work that
never earned it.

**And the integration milestone must come out of this rework with the HIGHEST number in the plan.**
The pipeline closes the last milestone's implementation automatically, and it finds "last" by the
maximum number — not by which milestone you wrote last. So if you add work, it takes numbers above
the integration milestone's, and the automatic close would fire on your new work instead. Drop the
integration milestone and re-add it above everything you added, with the next number in the
sequence the pipeline gave you.

### 4. Plan forward from what exists

The delivered milestones are the **landscape**, not a plan item. Write the remaining work as it
should be done *given that they exist and cannot change*. Do not re-plan around them as though the
project were starting over.

### 5. What happens to the score

Nothing, until the plan's review comes back clean. Then the count of milestones in the **new** plan
becomes the denominator, and **the delivered ones are credited immediately** at that denominator —
two delivered out of ten leaves **all six milestoned steps** (`30`, `31`, `40`, `41`, `50`, `51`)
standing at 0.20.

Nothing is rebuilt to earn that. It was built, reviewed and is now untouchable, so the credit is the
arithmetic catching up rather than a gift. **Do not attempt to grant it yourself** — it is computed.

---

## Reworking the MAP or the TEST PLAN

No partition, no immutability, no milestone arithmetic. Rewrite the named claim per that step's own
skill — `/10-context-map` or `/40-test-plan` — and change **only what the finding names plus what
that change makes wrong**. A rollback is not an invitation to rewrite the document you inherited.

**Then search the whole artifact for every other place that states the claim you changed.** A
document repeats the same fact in a summary, a table and a section body; fixing one of three leaves
it contradicting itself, which the next reviewer finds as a new finding. `grep` the key terms before
you close.

---

## Reworking the CODE — `93-rollback:30`

The review of the test plan or of the test run found this milestone's code wrong. No partition and
no milestone arithmetic: the milestone is not delivered, and its share at the later steps cleared
when this ticket opened. Rework the code per the finding as `/30-implement-plan` would — the
milestone's plan as the spec, the project's own patterns, the smallest change — and change **only
what the finding names plus what that change makes wrong**. A test the finding names is fixed with
the code.

Then the code review follows: an independent `31-review-impl` of this milestone opens when you
close, and after it the milestone's test plan, test run and their reviews run again.

---

## Closing

You do **not** review your own rework and you do **not** declare it clean. A fresh review of the
reworked step runs after you, and everything downstream is re-checked against it.

Append **one line** to the process log — the pipeline prints the exact line when the ticket opens.
It closes as a **fix**: status `fixed`, the counts saying what this rework discharged, and the **`QA`
tick**, which is you confirming the rework genuinely answers the finding rather than merely editing
around it. **No tick, no close.**

**Reworking the map or the plan** (`93-rollback:10` or `:20`) is writing it again, and it closes
as they do: before you close, ask every question that changes the work —
`python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" question ask "<what you need to know>"` — and
wait for the answer, then write the line `Open questions (<ticket>): none` on a line of its own in
`WORKING.md`, with nothing after `none` — `none` meaning every such question has been asked and its
answer recorded, and *decide later* being an answer. The close is refused without it, and the
refusal names the line.

## What this skill must never do

- **Edit a delivered milestone.** Ever, for any reason, including tidiness.
- **Reuse a milestone number**, including one dropped in this same rework.
- **Undo delivered code.** If shipped work must be reversed, that is a new milestone, planned and
  reviewed.
- **Rework the step that was reviewed.** That is `/92-fix`.
- **Grant score.** It is computed when the review closes clean.
- **Fix findings the reviewer did not raise.** If you see something else, say so; do not act on it.
- **Judge the findings you were given.** Not whether the rollback was warranted, not whether a
  finding holds. Discharge, report what you could not, and let the next review decide.
