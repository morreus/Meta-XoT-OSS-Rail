---
name: 31-review-impl-gated
description: GATED 31-review-impl — the /00-ship* variant, for use ONLY while a run is active. Invoke the plain /31-review-impl when there is no run. Adversarial fresh-eyes review of the IMPLEMENTATION (uncommitted working tree) against the plan, codebase conventions, git history, and the web. File-by-file; proves behaviour; severity-tagged. Run after /30-implement-plan, before /60-commit.
user-invocable: false
context: fork
background: false
disallowed-tools: Edit Write NotebookEdit
---
> **YOU ARE THE REVIEWER, INSIDE A GATED RUN.** This is the `/00-ship*` variant of the skill
> below. A turn-end hook is verifying this run and will not let the turn end until this review
> is genuinely closed.
>
> You are running as your own agent, with your own context. **You did not produce the work you
> are about to review, and you have none of the conversation that produced it.** That is
> deliberate: fresh eyes are the whole reason this stage is a separate agent — and the pipeline
> knows the difference, because the hook that saw this command run saw it come from inside a
> subagent. Nobody hands you a briefing, and nobody may: a reviewer handed its conclusion is where
> reviews go wrong. **You are scoped by the run's own records, which you can verify**, so read
> these five things, in this order, before anything else:
>
> 1. **What the project is** — the section `## 0. The request` of the working document,
>    `WORKING.md` at the project root, in the operator's own words.
> 2. **Where the run stands** — `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" status`, which
>    names the open ticket, its step, the milestone if the run is inside the branch, and the
>    exact line you will append when you close.
> 3. **What changed** — against the right point, and the right point is named for you.
>    - **A document** — the map, the plan and the test plan in `WORKING.md`, the results in
>      `TEST_RESULTS.md`, both at the project root: `status` prints a line
>      beginning `the document's copy:`. It names the copy the pipeline kept of the document as an
>      earlier review saw it — a copy no agent can write — and the command to diff it. **A fresh
>      review: what changed since the last fresh review; a review of your own fix: what changed
>      since the previous round** — `status` names the one you must diff against, and a fresh
>      round must use the last fresh review's copy it names, not the latest beside it.
>      `git diff --no-index --word-diff <copy> <the document status names>` keeps a one-word
>      change from marking a whole paragraph. *No copy* means the first review of a loop, or a copy that is missing or
>      altered: read the whole document.
>    - **Code** (step 31): the milestone is committed only when its last step closes clean, so
>      during its reviews it lives in the working tree. `<commit>` is the `commit` on the last
>      close in `.metaxotrail/events.jsonl` that carries one (the previous milestone's credit), or the
>      claim's `base_commit` on the log's first line if none does. Read it as the pipeline counts
>      it: `git status --porcelain --untracked-files=all` lists every changed and every new file,
>      `git diff <commit>` shows the tracked changes against the working tree, and every new file
>      is read in full. Not a range ending at `HEAD` — empty while the milestone is uncommitted.
>    - Then, either way, **search for the old wording** of every line the change touched, across
>      the whole artifact, and report every place it survives in one finding.
> 4. **What was planned** — the plan section for this milestone, in `WORKING.md`.
> 5. **What has already been found** — the issues file, `.metaxotrail/issues.jsonl`, one JSON entry per
>    finding so far.
>
> Every one of those is the run's own record. They bound the review without steering it.
>
> **You review. You do not fix.** `Edit`, `Write` and `NotebookEdit` are denied to you in this
> agent, and the hook refuses the artifact under review to a reviewer
> regardless. The point is not a wall against a determined agent but against the easy path, the
> "while I am here, this is a one-line fix" that turns a verdict into something nobody can
> interpret: nobody can then tell whether the work was right or whether you made it right on the
> way past. Repairing is a different step with a different agent, and it has to prove each fix.
>
> If `status` refuses because the event log is not there — there is **no active run** — you were
> invoked by mistake: say so and stop; any other refusal, show it and stop.
>
> Now carry out the skill exactly as written. How this review is closed is at the end.

---

ultrathink: Adversarially review the implementation for: $ARGUMENTS — with your own receipts.

## Prerequisites
- A plan exists in `WORKING.md` and there are changes to review — uncommitted, or committed
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

---

## Closing this review under the gate

You have a shell and the run's records; you have no `Edit`, `Write` or `NotebookEdit`. Three
writes close a review, all three from the shell, all three appends, nothing that rewrites a file.

**1. Every finding goes to the issues file**, `.metaxotrail/issues.jsonl` in the project — one JSON
line each, **four fields**: the ticket, the severity (`HIGH`, `MEDIUM` or `LOW`, by the
severity test in the skill above), the finding, and the proposed fix. The fixer opens by
reading these; a finding with no proposed fix is a finding it has to rediscover.

```bash
echo '{"ticket": "31M1V1", "severity": "HIGH", "finding": "...", "fix": "..."}' >> .metaxotrail/issues.jsonl
```

A review that finds nothing writes nothing here, and that is the good outcome — not an error.

**2. Append ONE line to the process log**, `.metaxotrail/process.log`. `status` printed its object with
the ticket and `"status": "reviewed"` filled in; **you add the counts** — `"h"`, `"m"`, `"l"`,
your HIGH, MEDIUM and LOW — and a note after the closing brace. The pipeline never fills counts
in: a pipeline writing `0H 0M` would be writing your verdict.

```text
{"flag": "", "h": 0, "m": 1, "l": 2, "status": "reviewed", "ticket": "31M1V1"} one MEDIUM, the null case at the boundary
```

**A rollback is ordered by the flag you TYPE on the close, and the line carries the same flag as
your record of it.** If what is wrong is not the step you reviewed but the document it was built
from, put `"flag": "ROLLBACK <step>"` on the line — the bare step number, `ROLLBACK 20` — **and
type it on the close below.** A line saying `ROLLBACK 10` under a close typed without it
opens an ordinary `92-fix` and says nothing — the pipeline reads the act off the command. A
rollback needs a finding: a line ordering one with `0H 0M` is refused.

**Which rollbacks each review can order** — only to a document earlier than the one it reads:

| Review | May order |
|---|---|
| `11-review-map` | nothing — it reads the first document; what is wrong there is a fix |
| `21-review-plan` | `ROLLBACK 10` |
| `31-review-impl` | `ROLLBACK 20`, `ROLLBACK 10` |
| `41-review-test-plan` | `ROLLBACK 30`, `ROLLBACK 20`, `ROLLBACK 10` |
| `51-review-tests` | `ROLLBACK 40`, `ROLLBACK 30`, `ROLLBACK 20`, `ROLLBACK 10` |

**`ROLLBACK 30` is the way back to this milestone's code.** When the test plan or the test run
shows a defect in the code, order it: a fix of the test plan or of the results cannot mend code,
because nothing at those steps reviews code. The code is reworked at its own step and the code
review reads it again, then the milestone's later steps repeat. It reaches only a milestone not yet
delivered; on a delivered milestone's ticket the close is held and the operator is asked.

**3. Close the ticket from inside this agent**, typing the counts you wrote and, if you are
ordering one, the rollback — this is what opens the repair:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" close reviewed 0 1 2
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" close reviewed 1 0 0 "ROLLBACK 20"
```

The hook that saw this command saw it come from a subagent; that is what lets the close through,
and it is not something you claim or type. **A refusal names the legal next move** — a line that
disagrees with the counts you typed, a rollback to a step this review cannot reach. For the
second, do not narrow the target to make it legal: ask —
`python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" question unreachable "<what you found and where it belongs>"`
holds the ticket and gives the operator the legal instructions to order it themselves.

**A reviewer never asks a content question.** `question ask` is refused on a review ticket by the
pipeline itself: what you need to know is in the run's records, and what is not there is a finding,
not a question.

**Write every path outside the project in full.** The hook that judges each write does not read
shell variables. In `SC=/tmp/x; echo a > $SC/out.txt` it judges a file named `$SC/out.txt` inside
the project, refused while the code is under review; after `cd $SC` it cannot tell where the shell
stands, and a relative write after it is refused at any step. Write `echo a > /tmp/x/out.txt` and
`cd /tmp/x && …` instead. To work on a copy of the project, make it with
`mkdir -p <full path> && tar -C <project> -cf - --exclude .metaxotrail . | tar -x -C <full path>` —
`tar -x -C` needs the folder to exist. While the code is under review `cp` or `ln` of a project
file is refused, and `git archive HEAD` copies the last commit, not the change under review.

If there is **no active run** — `status` refuses because the event log is not there — you were
invoked by mistake; say so and stop.

You review. You do not fix, and you do not close anything but your own ticket.
