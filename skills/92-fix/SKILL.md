---
name: 92-fix
description: Fixes the problems a review rated high or medium, with small, targeted changes, then hands the work back for a fresh review. It does not review or approve its own fix.
disable-model-invocation: true
argument-hint: <stage/artifact, or "the last review's findings">
---

Apply the review findings for: $ARGUMENTS

You are the **fixer half of the review loop**. A read-only review (`/11-review-map`, `/21-review-plan`, `/31-review-impl`, `/41-review-test-plan`, `/51-review-tests`) produced findings; your job is to **correct the artifact, not judge it**. A fresh review runs AFTER you — you do NOT self-certify or declare clean.

## Which stage, and so which artifact and which proof

**The stage is read, not guessed.** The review you were handed names the artifact it reviewed,
and that is the produce step whose row applies — the one whose artifact you are fixing and whose
proof obligation holds. One row applies, and the obligations differ, because *prove each fix* is
written code-shaped and for a document none of it fits:

| produce step | the artifact | the proof obligation |
|---|---|---|
| `10-context-map` | the map, in `docs/context_map_<slug>.md` — per `/10-context-map` (evidence, receipts, true unknowns marked) | **the sweep**: grep every other place that states each fact you changed, and update them in the same pass; record the sites |
| `20-plan-impl` | the plan, in `docs/context_map_<slug>.md` — per `/20-plan-impl` (options, assumptions, milestones, pre-mortem) | **the sweep**, as above — a plan restates a fact in a summary, a table and a section, and a fix that reaches one of three is hidden, not discharged |
| `30-implement-plan` | the code — per `/30-implement-plan` (minimal diff, existing patterns, the stack's instrumentation style) | **reproduce, trace, check the callers**: trigger the exact failure and watch it stop; follow the path for the input named; every changed symbol's callers |
| `40-test-plan` | the test plan, in `docs/context_map_<slug>.md` — per `/40-test-plan` (coverage, arrangeable preconditions, measurable criteria) | **the sweep**, as above, plus: every precondition you changed can still be arranged |
| `50-test-impl` | the results, in `docs/test_results_<slug>.md` — per `/50-test-impl` (real evidence, honest verdicts, no live actions) | **re-run**: the test the finding names, run again, with its real output pasted — a result is never edited into passing |

**Which file.** `<slug>` names the work: the context map document is the one `/10-context-map` wrote for it, and the results file carries the same slug. If `docs/` holds more than one context map document and neither the request nor the conversation says which, ask.

## Inputs
- The latest review's findings (fix all **High/Med**; a **Low** only under the Low rule below), each with its severity
  and its **proposed fix** — you open by reading them, all of them, before you touch anything.

**Before fixing a claim, and again after it, search the whole artifact for other places that state it.** A document
restates the same fact in a summary, a table and a section body, and fixing one of the three
leaves the artifact contradicting itself — which the next reviewer finds, correctly, as a new
finding. `grep` the key terms of what you changed
before you close the round; do not trust your memory of where you said it.
- `${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md` + `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md` and `CLAUDE.md`.
- **The working document is written INTO, never over.** Edit the sections the findings name, and
  never open it by overwriting.

## Rules
- **Only the findings.** Address each High/Med; no scope creep, no "while I'm here" edits.
- **The Low rule.** A Low is corrected only when the fact it corrects is stated in one place — found
  by a search before the edit — and the correction adds nothing, not even a rule the reviewer
  proposed: it only puts right what is already there, a wrong count, a stale name. Every other
  Low is logged — its finding number and its first words, in one line of the record of the repair. Fixing every Low grows the text the next review reads, and a spreading correction
  is where a fix writes the next round's findings. When the operator orders Lows fixed, their order
  stands over this rule.
- **Minimal diff**, match existing conventions (`_shared.md`).
- **Don't introduce new problems.** For code, do a quick sanity check that it still compiles/imports/runs — but leave the real verdict to the fresh re-review.
- **Record what changed** (each finding → the fix) in the working document's record of the repair (a *Record of the repair* heading — add it if missing), **and list
  the sections you edited** — that list is the next reviewer's starting point. Cite a section and a
  short quoted phrase, never a line number: line numbers move with the next edit, and a stale one is
  a finding against your record. A code fix cites the file and the symbol.
- ⚠️ **A fact you change is probably written down more than once. Find the copies.** The recurring
  failure in these documents is not a wrong fix — it is a fix that lands in one place while three
  others keep contradicting it. Before you finish, for every *fact* you
  changed — a status, a count, a decision, a line number — grep the artifact for its other
  statements and update them in the same pass. Record which sites you found and updated, so a
  reviewer can check the sweep rather than rediscover it one round later.
- **A finding against an already-closed milestone: decide whether it is a bug or a design defect,
  and say which.** Each milestone is carried all the way through — implemented, reviewed,
  test-planned, that plan reviewed, tested, results reviewed — before the next starts, so by the
  time a later milestone (often the plan's final integration milestone) exposes a problem in an
  earlier one, that earlier one is closed and credited.
  - **A bug** — it did what it set out to do and there is a defect in it → fix it **here**, in the
    milestone you are in, when this repair is of its code (step 30) — the milestone's own code
    review covers the change. Record which milestone's code you changed. That is ordinary
    release-candidate work. Found while repairing the test plan or the results, it waits for the
    code step — the next rule.
  - **A design defect** — the approach was wrong, or the exit criteria were never really met → **do
    not fix it here.** Stop and say so: that milestone has to be redone, not patched. A rollback
    is ordered by a review — the re-review that follows you can order it on its own record — or
    by the operator, and it takes the credit off everything built on the document that was wrong.

  The lax direction is the costly one: quietly repairing closed milestones inside the current one
  makes their reviews meaningless and leaves the score claiming work that is being repaired behind
  it. On a close call, say so plainly and let the re-review challenge you.
- **A defect in code found at steps 40 to 51 is not fixed in that repair** — in this milestone's
  code or a closed milestone's. The next review reads the test plan or the results, not code, so a
  code change made here is reviewed by nobody. Leave the code as it is, record the finding as not
  discharged in your record of the repair (inside a run: in your close line's counts and note), and say so: the re-review orders `ROLLBACK 30` (in a `/00-ship` run), which
  sends this milestone back to its code step, where the fix is made and the code review reads it.
  Test files belong to the test run and are fixed with it. If every finding of the round is such a
  defect, there is nothing to discharge, so this repair cannot be finished: say so plainly, and the
  review runs again to send the milestone back to its code.
- **Respect safety.** Never touch secrets or perform irreversible/production actions to "fix" something; destructive git/`rm` triggers a confirmation prompt to the operator.
- **Stuck?** If a High/Med can't be resolved (the fix doesn't work after honest attempts, or it's a genuine design problem), **STOP and warn the user** with the blocker — per the "Stuck = stop, don't ship" rule in `_shared.md`. Don't loop forever or fake it.

## PHASE 1: PLAN THE REPAIR — before the edit

A fix that edits first and searches only afterwards is how a repair writes the next round's findings:
a claim nobody measured, a rewritten section that dropped something another section relied on, a new
rule contradicting an old one. So for every High and Medium, before you change a
word, work out four things — the plan's evidence, assumptions and pre-mortem (`/20-plan-impl`),
asked of one repair:

1. **Every place that states the fact** — search the whole artifact now, before the edit. The sweep
   after it (Rules) still runs, for the copies your edit wrote. A document restates a fact in a
   summary, a table and a section body.
2. **The change** — what you will write, and in which of those places.
3. **Every new behaviour claim the change will write, and how it will be measured.** A behaviour
   claim that cannot be measured is not written. An unknown, an assumption or a question is written
   as one, with its confidence — never as a fact.
4. **What relies on what changes, and what the change could contradict** — the sections that build
   on it, and the rules, assumptions and decisions it touches.

The plan stays in your reply. It is not written into the artifact: everything in the artifact is
read by the next review, and a plan written there becomes one more thing to find fault with. The
artifact gets its result, in the new-facts table below. Then edit, to the plan.

## PHASE 2: PROVE EACH FIX — you OWN these repairs

You are not a typist for someone else's findings. You own the repair, and a repair you have not
checked is a guess handed to the next reviewer. The review is the police; you are the one who has
to satisfy them that the thing they stopped you for is actually fixed.

**For every High and Medium, produce this — one row each, no exceptions:**

| # | The finding, quoted | What changed (a section and a quoted phrase; for code, the file and the symbol) | How you PROVED it is fixed | Evidence |
|---|---|---|---|---|

**"How you proved it"** means you made the failure the reviewer described, and watched it stop
happening. Not "the logic now looks right". The three that count:

1. **Reproduce, then re-run.** If the finding named a concrete failure — a wrong value, a crash, a
   case that slipped through — trigger that exact case and paste the REAL output, before and after
   if you have it. A finding you cannot reproduce is a finding you cannot claim to have fixed: say
   so in the row rather than asserting.
2. **Trace the path.** For a finding about a code path, follow it for the input the reviewer named
   and for the edge they were worried about. Naming a function is not tracing it.
3. **Check the neighbours.** Every changed symbol: who calls it, what did they expect. A fix that
   breaks a caller is a worse finding than the one you closed.

**And a second table — the new facts the fix wrote.** A fix writes new text, and new text carries
new claims. List every new fact your fix put into the artifact — a
count, a name, a location, a behaviour, a decision — where it now stands, every other place that
states it, what it could contradict and where you checked that, and the command you ran or the line
you opened that shows it is true. The two middle columns are PHASE 1's result:

| # | New fact the fix wrote | Where it stands (a section and a quoted phrase; for code, the file and the symbol) | Every other place that states it | What it could contradict, checked where | The command run or line opened |
|---|---|---|---|---|---|

Write this table into the record of the repair in the artifact too, beside the list of sections you
edited, so the next reviewer reads it where it reads the fix. A fix that wrote no new fact says
`none` there — it does not leave the table out.

⚠️ **A fact you changed is probably written down more than once.** The sweep rule above (Rules) is part of
proving the fix, not a tidy-up after it: if the correction reached one section and three others
still contradict it, the finding is not discharged, it is hidden.

**Then say, explicitly, one of these two things:**

- **"All High/Med discharged and verified — ready for re-review."** Only if every row above has
  real evidence in it. This is your signature on the repair. It does not certify the review's
  verdict — that is the next reviewer's job — it certifies that what you changed does what you
  say it does.
- **"NOT ready — <which findings, and why>."** If a fix is unproven, partial, or you could not
  reproduce the failure, say that instead. An honest "not ready" costs one round. A false "ready"
  costs the reviewer's time and, if it slips through, the operator's trust in every green result
  after it.

Never hand over with the rows blank or the evidence column reading "should now work".

## Output
- The findings table above, filled in.
- The new-facts table, filled in or `none` — here and in the record of the repair.
- Your explicit verdict: **"All High/Med discharged and verified — ready for re-review"** or
  **"NOT ready — ..."**.
- **"BLOCKED: <reason>"** if you are stuck and need the operator.

Do NOT re-review here — the fresh-eyes review still runs, and it decides. Owning the repair means
proving what you changed; it does not mean closing the stage.
