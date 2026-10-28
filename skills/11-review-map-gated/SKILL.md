---
name: 11-review-map-gated
description: GATED 11-review-map — the /00-ship* variant, for use ONLY while a run is active. Invoke the plain /11-review-map when there is no run. A second Claude reviews the study written by /10-context-map. It re-checks the code, the git history and the web, questions every claim, and lists gaps and open questions. Use it before planning.
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

ultrathink: Adversarially review and challenge the context map for: $ARGUMENTS — with your own receipts.

## Prerequisites
- [ ] `WORKING.md` exists (from `/10-context-map`).

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
