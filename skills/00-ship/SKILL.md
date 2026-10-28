---
name: 00-ship
description: Takes a feature or change from idea to finished, tested code. Claude studies the project, plans, builds and tests the work, and a second Claude reviews every step. The run cannot skip a step or stop early, and it asks you only what is yours to decide. For a small change, use /00-ship-lite.
disable-model-invocation: true
argument-hint: <feature / change>
---

# 00-ship — gated feature pipeline (full chain)

**A run works only in Claude Code**, where the plugin's hooks guard it. If a pipeline command fails because
`pipeline.py` is not there, say in one line that a run needs Claude Code, and stop: do not carry out the run's
steps without the pipeline.

The pipeline is a **score vector**, one number per step. **You never write the score** — the
pipeline computes it from its own event log, which you cannot edit, and a turn-end hook blocks the
turn from ending until the vector reaches its target.

## The scoring rule
For N steps, **step i's maximum is N − i + 1** — the full chain of ten targets `10,9,8,…,1`.

> **score_i = the number of distinct steps k ≥ i that have completed cleanly since step i was last rolled back.**

- **Clean completion of step j** → +1 to step j and every earlier step that has not already been
  credited for j.
- **Open questions / findings** → no change.
- **A rollback to step k** → when its repair opens, steps **k+1…N** lose their stage credit and
  step k keeps its own. Inside the milestone branch (30, 40) only the current milestone's share
  clears; before it (10, 20) the milestones' shares wait for the re-plan's clean close, which keeps
  the delivered ones. The earlier steps stay complete, and each one's score counts what is still
  complete after it.
- **Order is fixed** — the pipeline opens the next step itself when the previous one closes; you
  open nothing and skip nothing.

A step's score therefore means *"how much downstream work has since confirmed it"* — the plan is
only fully proven once the implementation and its review landed without sending work back.

## The chain
**full (10):** 10-context-map · 11-review-map · 20-plan-impl · 21-review-plan · 30-implement-plan ·
31-review-impl · 40-test-plan · 41-review-test-plan · 50-test-impl · 51-review-tests
**lite (6)** stops after 31 — that is `/00-ship-lite`, and choosing it is choosing to ship code that
was reviewed but never tested.

Steps 30 onward run **per milestone** of the plan, each carried all the way to its last review
before the next milestone starts. When the plan has more than one milestone besides M0, its **highest-numbered milestone builds nothing**: it is
the integration pass, its step 30 is closed by the pipeline at the open, and its reviews are the
end-to-end ones.

## You MUST use the step skills — improvising will not pass the close
For every step, **invoke the `<id>-gated` skill** and follow that method. Do not work from memory
or from the pattern of an earlier step. The close checks the working document for the sections
that skill mandates and refuses, naming what is missing, if you improvised. **A review step you
do not do at all**: invoke its `-gated` skill and nothing else — it runs in its own agent, reads
the run's records, writes its findings and closes its own ticket from inside that agent. **Do not
wrap it in an `Agent` call**: the one thing a wrapper adds is a prompt you write, and a reviewer
handed its conclusion is where reviews go wrong.

## What the pipeline is, in this project

- `WORKING.md` at the project root — the **one** working document: map, plan and test plan, as
  sections of one file. `init` creates it (or stamps it) with the run's hash in its first line;
  every skill writes INTO it and never rewrites that line.
- `TEST_RESULTS.md` at the project root — step 50's results, carrying the same hash.
- `.metaxotrail/` in the project — the books: `events.jsonl`, the pipeline's own record, which you never
  write; `process.log`, where you append one line per close; `issues.jsonl`, where reviewers
  append findings. The write hook refuses an agent's edits to the run's records and to the artifact a
  review is reading, and it refuses `git` commands that would undo credited work.

## Commands (this is your whole interface)
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" init <chain> [<start step> [<milestone>… | none]]
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" status      # the open ticket, who may write, THE LINE TO APPEND, the score
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" close <status> [<h> <m> <l> [<flag>]]
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" question <kind> "<text>"   # hold the run and ask the operator
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" report      # the run's history — every close, and which were attested or overridden
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" bind        # move the gate to THIS window
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" archive [--abandon]   # end the run (/94-clean-process)
```
There is no `begin`: the open is the pipeline's, recorded when the previous step closed. **Every
command applies the operator's pending answer first** — so after they reply to a question, running
`status` is enough to have it acted on, and `report` says what it did.

## STEP 0 — look before you ask. The disk already knows which situation this is.

`init` freezes the chain, records the base commit and attests whatever is adopted; getting it
wrong means starting over. So the first act of this skill is to **read the project**, and only
then put a question. There are three situations and no others:

| what is on disk | the routes, and there are no others | may it offer a starting step? |
|---|---|---|
| `.metaxotrail/` holds a **live run** | **take the run over in this window** (`bind`, then `status`) — or **end it** (`question end`, then `archive --abandon` on their `OVERRIDE END`) | **NO** |
| records whose run has **ended**, or none, with prior work on disk | continue: a new run adopting what is done — or a new run from the beginning, `init full`, no start step | yes |
| nothing | a new run from the beginning — `init full`, no start step | yes |

**The first row.** A run that is live belongs to a window — the one that started it, or the last
one that bound it. A tab that was closed, cleared or lost leaves the run intact and the binding
naming a window that no longer exists; this new tab is then **not gated at all** until the binding
moves, which is the state hardest to notice and worst to be in. The route is `bind` followed by
`status` and nothing else — no `init`, no chain, no starting step, no attestation, because none of
it is being created. `init` refuses over a live run. The other route is to end it: ask `question end "<why>"`,
and on their `OVERRIDE END`, `archive --abandon` records the ending and the score it reached. **No starting-step menu is shown on this
row** — choosing a step on a live run would take credit off that step and every one after it, which
is a rollback wearing a resume's clothes, and a rollback is a review's to order.

**The second row — adoption.** Prior work exists: a `WORKING.md` from an ended run, or documents
from before this pipeline — a context map document, `docs/context_map_<slug>.md`, which is also
where the step skills write when they are used without a run. Look, then propose:

| What the document already contains | Where the run should start |
|---|---|
| nothing, or no document at all | **no start step at all** — `init full` — a start step means adoption, and there is nothing to adopt (`init full 10` is refused when there is no document) |
| a context map, unreviewed | step 11 — the review of the map |
| a context map they say was reviewed — by `/11-review-map` without a run, say — and no plan | step 20 — the plan |
| a map and a plan | step 21 — the review of the plan |
| a reviewed plan, no milestone finished | step 30, `none` — implement the first milestone |
| milestones already finished | step 30, naming the finished milestones |
| a milestone's tests run, its results in `docs/test_results_<slug>.md` | step 51 — the review of the results, naming the finished milestones or `none`; the results migrated into `TEST_RESULTS.md` under rule 3 |

### What the operator sees — a short briefing and the sheet

Everything above is yours to work out; the operator is shown the conclusions. Send **one message**:
**a short briefing** in the chat (`${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md`, "Brief before you ask") and
**the sheet** (`AskUserQuestion`), which **one click** answers. The briefing says what you understood, what
earlier work there is, in plain words, and what each start choice means — a few lines; never what you are
checking, never *I'll look at what's on disk first*. The business line stays in the sheet question's own text,
so it is on the sheet every time:
*We are building: <what, in their words>. How do we start?*

**They may have no experience of MetaXoTRail or of how software is built** — MetaXoTRail is there to help them build
something — so what they are shown is written for them: plain words, and what happens next said **in the
order they will see it**. Step numbers, skill names, *run*, *chain*, *full*, *lite*, *adopt*, *map*,
*ticket*, *milestone*, *reviewer*, *references*, line numbers, *on disk*, file names, commands and
settings stay in these instructions and never reach the briefing or the sheet. Say instead: *Claude studies the project and writes down how it works* (the map), *plans
the change* (the plan), *builds and tests it one part at a time* (the milestones), *you are asked
before each important choice*; *the notes and the plan we made* (an adopted document); *the first
part of the plan* (M1); *your notes match the code* (the references are right); *a second Claude,
starting from nothing, checks them* (an independent review).

- **Shipping:** what is being shipped, in one sentence — the thing you have been discussing, or
  what they pointed you at — so the operator can see you have the right thing. They read it as the
  question's first words, *We are building: …*, in plain words and with no file name. It NAMES the request
  and never replaces it: `## 0. The request` records their own words for it, verbatim — their argument
  to this skill and what they said — never this sentence, and an adopted document's §0 stays as it
  is. The map review reads its scope from those words, list and all.
- **The sheet** — one sheet question, headed by a plain word such as `Start`, never `q<n>` (the
  form a run's own questions use), asking **new run or continue**. Its options come from the row
  of the table above that the disk matched, **each in business words**:
  - **Start fresh** — a new run from the beginning: the third row, or the second when they start
    again. Its description says what will happen, in their words.
  - **Use the work we made** — the second row, adopting: **one option per real path, up to four**
    in all, *Start fresh* and *Tell Claude more first* among them — so two paths of work on one
    question — each a whole path in their words, from the adoption table above — *Check the notes first*
    (step 11), *Plan from the notes* (step 20, only where they say the notes were checked), *Check the
    plan, then build* (step 21), *Build on the plan* (step 30, `none`), *Continue with part 3*
    (step 30, the finished milestones named: *parts 1 and 2 are built*), *Check the test results*
    (step 51). **Which document and which step** sit behind each option and never on it. **Inside
    the implementation branch — step 30 or after — the finished milestones, by name, or none**, go
    in its description, as the parts already built, each by what it does. Propose them; **do not
    infer** them silently. Where two earlier works could be meant — an ended run's and a context map
    document — each is its own option. Earlier work is copied, never reworded (rule 2 below), and
    redoing it is the option that checks it again or starts from the beginning, so copy-or-rewrite
    is never asked. Anything else `init` needs goes in the description, as a proposal. The paths that
    fit go on the sheet, the likeliest first; **a second question on the same sheet only when two
    things are both unknown** — which earlier work, and whether it was checked — and never a third.
  - **Resume the paused run** — the first row: `bind`, then `status`; no step is proposed.
  - **End it** — the first row. Its description says, in plain words, that it stops the earlier
    attempt and that what was done is kept, so a new start can use it. Their click is your reason to
    ask `question end "<why>"`; then write in the chat the one line they paste to confirm, on a line
    of its own: `OVERRIDE END` — and, for a change of mind, the line that keeps the run going instead,
    the `OVERRIDE OPEN` reply `question end` printed. Their pasted line is their answer, recorded in every
    mode; on `OVERRIDE END`, `archive --abandon`. No second sheet.
  - **Tell Claude more first** — wherever new work is about to start (the second and third rows),
    one more option: they add details about what they want before anything starts. On their click, ask
    them for those details in a sentence; their words join the request — in a new run `10-context-map`
    records them in `## 0. The request` with the rest of their own; when adopting, they are written
    verbatim beneath the adopted §0, under a dated line *Added at the opening*, before `init` — and
    the sheet is sent again, with what they said in it.

  Only the options the disk allows are offered — a live run gets *Resume* and *End it* and nothing
  else — the recommended one first, its label ending *" (Recommended)"*, each label one to five
  words and its description saying what it does and what it leaves.

The assessment of an adopted document (below) is shown **only when adopting**, in **at most three
lines** — three short sentences — in the briefing: what is solid, what is thin, what you
could not check.
Setup the operator did not ask about — which files you read, which commands you will run, `init`,
setting files aside, how the pipeline works — **is not narrated**. A reply under
*"Other"*, or typed, is their input and not a choice: read it, and send the sheet again with their
correction in it — if they name a different step, use theirs; it is their call. A click that does not
name the finished milestones has not named them. Where no sheet can be shown, type the same options
under the numbers `1`–`4`, never the letters — a letter is a running question's key, and the prompt
hook would record it as their answer there — and take their number. **You do not run `init` without their
explicit approval**: their click on an option, or their number — not "they did not object". And **their click
is the go-ahead**: do
the setup at once — the copies, the files set aside, `init` — without asking again and
without describing it; the next thing they see is the first stage's work, in plain words.

For example, in a project with nothing in it yet:

> The briefing, in the chat — *You want a CSV export for the orders page. There is no earlier work on this,
> so Claude starts from the beginning.*
>
> The sheet, one question — *We are building: a CSV export for the orders page. There is no earlier
> work on this. How do we start?*
> - **Start fresh (Recommended)** — Claude first studies the project and writes down how it works,
>   then plans the change with you, then builds and tests it one part at a time. You are asked
>   before each important choice.
> - **Tell Claude more first** — add details about what you want built. Nothing starts until you
>   choose again.

And where the last attempt left a plan that was checked:

> The briefing, in the chat — *You want the CSV export for the orders page, as we discussed. The plan from last
> time has been checked. Solid: each part says when it is done and how it is tested. Not checked: the largest
> export it allows. Using it, Claude builds its first part next; starting fresh, Claude studies the project
> again.*
>
> The sheet, one question — *We are building: the CSV export for the orders page, as we discussed.
> How do we start?*
> - **Use the plan we made (Recommended)** — the plan from last time has been checked; Claude
>   builds its first part next.
> - **Start fresh** — the earlier work is kept, and Claude begins again by studying the project.
> - **Tell Claude more first** — add details about what you want built. Nothing starts until you
>   choose again.

### Adoption needs the papers at the designated path, and you put them there BY COPYING

`init` reads the working document at `WORKING.md` and refuses an adoption whose document is not
there: adoption stands on artifacts that exist. Work done before this pipeline lives elsewhere —
`docs/context_map_<slug>.md`, where the step skills write when used without a run — so it is **migrated**, under three rules:

1. **The originals are copied, never moved.** The first act of a run must not destroy the thing it
   is adopting. Write a line in the new document saying where each section came from.
2. **It is a simple copy and nothing is reworded.** The required heading, then the operator's own
   text underneath, unchanged — so what they attest is what they wrote, and checking the migration is
   reading a diff that contains only headings, and the dated lines beneath §0 that they added at the
   opening. An adopted section that turns out thin is found
   when the work reaches it, and a rollback re-opens that step; there is no pre-emptive refusal.
3. **Migration happens only where there is no `WORKING.md`.** If one exists and it is the work
   they mean, it IS the document, and nothing is copied over it — the ordinary case, since an ended
   run leaves its document behind, and `init` replaces that document's header rather than the
   document. **But when the work they mean is a context map document and `WORKING.md` is an ended
   run's** — its first line is a run's header, `<!-- metaxotrail-run: … -->`, and no run is live —
   propose, in the description of the option that adopts their work, **setting it aside** — in
   business words, *the last run's notes are kept, renamed*: renamed to the first free
   `WORKING.md.aside-<n>`, the name `init` itself uses, never deleted and never
   overwritten — `init` then moves it into `.metaxotrail/` unless git tracks it, so the delivery commit
   cannot take it; then migrate their work under rules 1 and 2. **The results go with it**: an ended
   run's `TEST_RESULTS.md` is set aside the same way, to `TEST_RESULTS.md.aside-<n>`, so a results
   file left behind is never reviewed as theirs. **And wherever the run will start at step 50 or
   later** — over an ended run or in a project that never had one — their
   `docs/test_results_<slug>.md` is copied into `TEST_RESULTS.md` under rules 1 and 2: `init` keeps
   and restamps whatever results file it finds there, and refuses a start at 50 or later with none. A `WORKING.md` with no run's
   header is their own, and which one they mean is asked, not guessed. **Nothing this skill does can overwrite
   a document the operator already has.**

### Read the material before you propose adopting it

**Read it; never run it.** The opening only reads: no code and no tests of the project run before
their click — what running would show is found by the work after it.
You may only propose adopting a step you have actually assessed. Open the document and check it
against **that step's own skill** — `10-context-map` for the map, `20-plan-impl` for the plan —
the way a reviewer would, not by looking for headings. Say what you found — in the one message, in
at most three lines — three short sentences: what is solid, what is thin, what you could not verify. **If a step does not hold up, do not propose adopting it: propose
starting there.** Redoing a map costs one step. Building on a map that was wrong costs the run.

### What adoption does

`init full <step>` closes every step before `<step>` as **attested** — by the operator, on their
word, and `report` marks every one of them `ATTESTED BY THE OPERATOR, not checked`. That marker
is the difference, three weeks later, between a true answer and a false one about how a bug got
through. **Adopted milestones are the largest claim the system can hold**: `init full 30 M0 M1`
credits M0 and M1 across all six of their steps and this run verifies none of them. Only adopt a
milestone whose exit criteria you know were met; if unsure, leave it out and let the run carry it.

Then, and only then:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" init full <start step> [<milestone>… | none]
```

## Procedure
1. `init` once, then always `status` to find the open ticket.
2. Work **only** the open ticket: **invoke the `<id>-gated` skill** and carry it out. Each gated
   skill ends with how its ticket is closed — the line to append and the `close` to type. A
   review ticket cut to `independent` is the reviewer's to close, from inside its own agent; a
   close on it from here is refused by name. A review ticket cut to `orchestrator` — the round
   after your own fix — is yours to carry out and close, and a clean one opens a fresh
   independent round.
3. What opens next is the pipeline's decision, not yours: a clean independent review opens the
   next step; a review with findings opens `92-fix` on the step reviewed, and after your fix the
   same review again as your own round; a review that ordered a rollback opens `93-rollback` on
   the earlier step.
4. When the pipeline **holds the run and asks**, show the operator the question and the legal
   replies `status` prints — on the sheet, as the closing section of the `-gated` skill says: their click is their answer, and the
   key printed beside their choice, or a form below, is the typed fallback. **They answer with an
   instruction, not with "yes"** — an override
   **names an action rather than agreeing to one**:
   - `OVERRIDE ROLLBACK <step>` — they order a rollback the reviewer could not reach, or a
     different one.
   - `OVERRIDE CLOSE <ticket>` — they close the ticket they name on their own authority.
   - `OVERRIDE OPEN <ticket>` — they void the ticket the pipeline cut and open the one they name.
   - `OVERRIDE END` — they end the run short of its target, answering `question end "<why>"`;
     `archive --abandon` is refused until they have. That question's other reply, `OVERRIDE OPEN <its ticket>`,
     keeps the run going: nothing ends, and the run's next step is not held.
   - `ANSWER <your answer>` — their answer to a content question (`question ask`, a decision
     about the work that is theirs). It authorises nothing; the agent that asked reads it off
     `status` and finishes the step.
   A reply of *"20"* or *"do it"* is read by nothing; the ticket stays held.
   **Ask once, then wait in silence**: show the question once, end the turn and write nothing more until they
   reply — no reminder, no new question. When they reply, run `status` and see `answered q<n>`, or the move
   applied, before you say it was recorded; then drive the run on to its target. Their words under "Other" follow
   the closing section of the `-gated` skill: at an observation those words are their answer; at a decision, bring them
   back on a new question sheet.
5. Report the score after each close.

## Severity — the one test, in the words both parties read
A finding is BLOCKING if, shipped as it stands, the system would do something wrong. A finding is LOW if it is true, worth recording, and changes nothing anyone does. A defect nothing can currently reach is LOW unless the change under review also supplies the path that reaches it. A finding about how a document reads — wording, a stale line number or cross-reference, a copy that disagrees without changing what gets built — is LOW; a document finding blocks only when someone building from it would do the wrong thing.
The reviewers apply it; you read the same words, so that a finding graded differently by two
parties is an argument about the finding and never about the letters.

## What a review here is, and is not
A review closed from inside its own agent means exactly this: **the orchestrator did not write
this verdict, and the record shows a separate process did.** It does not mean the verdict is
right, and the pipeline does not check what the reviewer examined; it checks who closed the
ticket. Say it that way when you report.

## Completion
When `status` says **the chain is complete — nothing opens**: post the `/90-explain` summary
(issue / fix / why / impact / assumptions), show `report` and the delivered commits (`git log`), **do not push**
(never run `60-commit`: every part is already committed). **List every entry of `.metaxotrail/issues.jsonl` whose finding begins
`OUT OF SCOPE:`** — the findings a review recorded LOW as out of scope: outside the request, from
the map review, or outside the milestone under review, from the code review —
with the ticket that raised each and its proposed fix, under a heading *Out of scope — not done in
this run*, so they reach the operator as a backlog rather than stay in a file nobody reads —
the next `init` sets the issues file aside. Then output
exactly:
`SHIP-COMPLETE — score <final vector>; summary posted; commits not pushed`
`archive` ends the run, and `/94-clean-process` is the skill for it.

## Rules
- Never fabricate a close — the pipeline compares your line against your command and refuses
  the pair when they disagree, and the attempt stays on the record.
- Never perform irreversible / production / money actions.
- A rollback to an early step late in the run is expensive; when a review orders one, say so to
  the operator before the repair begins.

## Suggested `/goal` — paste this one line, nothing else
```
/goal Deliver «FEATURE» following the 00-ship skill — read it FIRST. Step 1: do STEP 0 of that skill — brief me in the chat, then show me its sheet, and WAIT for my click (or my number, where no sheet can be shown). Step 2: on my click, do the setup STEP 0 gives for the option I chose — `init full`, adopting what that option names, or `bind` if the run is live — exactly as the 00-ship skill spells the command (the skill carries the path; a pasted line cannot). Then repeatedly: run `status`, work ONLY the open ticket — you MUST invoke the `<id>-gated` skill and follow its method, and close the ticket the way that skill's tail says. DONE only when `pipeline.py status` says the chain is complete and you output a line starting SHIP-COMPLETE. If the pipeline holds the run on a question, show it to me once and WAIT in silence for my answer; then carry on to the target. Stop after 40 turns if blocked.
```
Replace «FEATURE».
