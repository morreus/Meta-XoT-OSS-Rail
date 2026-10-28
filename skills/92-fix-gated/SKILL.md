---
name: 92-fix-gated
description: GATED 92-fix — the /00-ship* variant, for use ONLY while a run is active. Invoke the plain /92-fix when there is no run. Fixes the problems a review rated high or medium, with small, targeted changes, then hands the work back for a fresh review. It does not review or approve its own fix.
user-invocable: false
---
> **YOU ARE INSIDE A GATED RUN.** This is the `/00-ship*` variant of the skill below. A turn-end
> hook is verifying this run and will not let the turn end until the open step is genuinely
> closed.
>
> **Before you do anything else, ask the pipeline where the run stands:**
>
> ```bash
> python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" status
> ```
>
> It answers with a few lines, among them: the open ticket and its step (`open: 10MXV1 at 10-context-map`),
> who may write, **the exact line you will append to the process log when this step is done**,
> and the score. Nothing is recorded by running it. You open nothing — the pipeline opened this
> ticket itself when the previous step closed, and the open is already on the record.
>
> If `status` refuses because the event log is not there — there is **no active run** in this
> project — you were invoked by mistake: stop, say so, and use the plain `/<step-id>` skill
> instead; any other refusal, show it to the operator and stop. Everything below assumes a run and will not make sense without one.
>
> **The findings raised so far in this run are in the issues file**, `.metaxotrail/issues.jsonl` in the
> project — one JSON entry each, with its ticket, its severity, the finding and the proposed fix.
> **On a `92-fix` ticket** the step `status` names is `92-fix:<target>`, and the part
> **after the colon** is the produce step whose artifact you are fixing: that is the row of the
> skill's table that applies, and the findings you discharge are the ones in the issues file
> against the ticket that reviewed it — read them all from there before you touch anything.
>
> If `status` says the run is **WAITING ON THE OPERATOR**, nothing you write will close this
> step: an earlier question is held open. Show the operator the question and the legal replies
> `status` printed, and wait. An override is applied by whatever command runs next; the
> answer to a content question is shown by `status` — `answered q<n>: …` — for you to work from.
>
> Now carry out the skill exactly as written. How this step is closed is at the end.

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
| `10-context-map` | the map, in `WORKING.md` — per `/10-context-map` (evidence, receipts, true unknowns marked) | **the sweep**: grep every other place that states each fact you changed, and update them in the same pass; record the sites |
| `20-plan-impl` | the plan, in `WORKING.md` — per `/20-plan-impl` (options, assumptions, milestones, pre-mortem) | **the sweep**, as above — a plan restates a fact in a summary, a table and a section, and a fix that reaches one of three is hidden, not discharged |
| `30-implement-plan` | the code — per `/30-implement-plan` (minimal diff, existing patterns, the stack's instrumentation style) | **reproduce, trace, check the callers**: trigger the exact failure and watch it stop; follow the path for the input named; every changed symbol's callers |
| `40-test-plan` | the test plan, in `WORKING.md` — per `/40-test-plan` (coverage, arrangeable preconditions, measurable criteria) | **the sweep**, as above, plus: every precondition you changed can still be arranged |
| `50-test-impl` | the results, in `TEST_RESULTS.md` — per `/50-test-impl` (real evidence, honest verdicts, no live actions) | **re-run**: the test the finding names, run again, with its real output pasted — a result is never edited into passing |

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

---

## Closing this step under the gate

The pipeline closes a step on **two records written separately and compared**: a line you append
to the process log, and the arguments you type to `close`. Neither is derived from the other. If
they disagree, the close is refused and the attempt is recorded with your line on it.

**1. Write the artifact INTO the working document.** `WORKING.md` at the project root was created
by `init` and carries the run's hash in its first line; the close checks that hash and the
headings this skill requires. Add your sections to it. Never rewrite its header and never open it
by overwriting — a rewritten header makes a later close fail, on an agent that did nothing
wrong.

**And the one line your close is refused without, where the step owes one.** `<ticket>` is the
ticket `status` names as open. The pipeline checks the line is THERE; it cannot check it is true,
and that half is yours.

- **A repair of a document** — `92-fix` on the map, the plan, the test plan or the results. Write
  the fix's new-facts table into the record of the repair, in the document it fixes, under the
  line `New facts (<ticket>):` on a line of its own, the table on the lines after it — or, if the
  fix wrote no new fact, `New facts (<ticket>): none`. Nothing else goes on that line: the close
  reads it whole, so `…: TODO` is refused. A fix of the code (step 30) owes no line.
- **The map and the plan** — `10-context-map`, `20-plan-impl`, and either one redone under
  `93-rollback`. Before you close, ask every question that is the user's to answer (`${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md`,
  "Ask, don't assume") with `question ask`
  (below) and wait for the answer. Then write, in `WORKING.md`, the line
  `Open questions (<ticket>): none` on a line of its own, with nothing after `none` — not a full
  stop, not what is still pending; the close reads it whole. `none` means every question that
  changes the work has been asked and its answer recorded. An
  answer of *decide later* is an answer, and it is recorded; the line does not claim nothing is
  left to decide. A question written into the document for somebody to find later is not asked.

**2. Append ONE line to the process log**, `.metaxotrail/process.log` in the project. `status` printed
the line — the JSON object, ticket and status already filled in — and you add a note after the
closing brace. The note is the one field nothing parses, which is why it lives outside the
object: one unescaped quotation mark inside would take the counts with it.

```text
{"flag": "", "status": "done", "ticket": "10MXV1"} the map — three sections, two unknowns
```

For a **repair** ticket (`92-fix`, `93-rollback`) the status is `fixed`, the counts say what this
round discharged, and the flag `QA` is your tick that each fix was proved:

```text
{"flag": "QA", "h": 1, "m": 2, "l": 0, "status": "fixed", "ticket": "92MXV1"} three discharged, evidence in the table above
```

**`92-fix` at 40 or 50 only — when every finding is a defect in code.** The skill above does not
fix code at those steps, so such a round discharges nothing, and a fix line that discharges nothing
is refused. Do not close it. Ask
`python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" question misopened "<the finding, and that the review should have ordered ROLLBACK 30>"`:
the operator's `OVERRIDE OPEN` of the review's next round voids this ticket, and that round
orders `ROLLBACK 30`.

**Step 20 only — if a run adopted at the plan has no map.** Then the plan skill's *stop without a
map* does not apply: open the document's sections with `## 0. The request`, holding the operator's
words verbatim, then an *Agreed context* section for what was settled in conversation. The plan
review and the code review both check the work against `## 0. The request`, so it has to exist and it has to be
what you were actually told.

**Step 50 only — the results file carries the run hash, and you write it.** The pipeline does
not create `TEST_RESULTS.md`, which the close reads at the project root. Put the run hash — the
value the pipeline printed when the run began, the same one in the first line of `WORKING.md` —
into the file's first line in exactly the form
`<!-- metaxotrail-run: <the run hash> -->`. The close refuses a results file without it: a stale file from
a previous run would otherwise close this step with no tests run. **Write no header if a header is
already present** — a run adopted at or past step 50 keeps its results file, and its header was
already stamped with this run's hash at the start; two headers in one file is the one shape the
check cannot see.

Append it — `>>` from the shell is the simplest way. One step, one line. A line that does not
parse does not count, and the close says so and names what it read.

**3. Close the ticket**, typing the status you wrote — and for a repair, the counts and the tick:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" close done            # a produce step
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" close fixed 1 2 0 QA  # a repair
```

A clean close writes the close and **opens the next ticket itself** — a produce step's review, a
repair's fresh review. You open nothing. `status` then names it.

**A refusal names the legal next move.** Read it and do that; do not retry the same command. The
conditions are the ones this skill mandates — the headings, the run hash, a line that parses and
agrees with what you typed, and for `30-implement-plan` a working tree that changed since the
previous milestone's commit.

**Write every path outside the project in full.** The hook that judges each write does not read
shell variables. In `SC=/tmp/x; echo a > $SC/out.txt` it judges a file named `$SC/out.txt` inside
the project, refused while the code is under review; after `cd $SC` it cannot tell where the shell
stands, and a relative write after it is refused at any step. Write `echo a > /tmp/x/out.txt` and
`cd /tmp/x && …` instead. To work on a copy of the project, make it with
`mkdir -p <full path> && tar -C <project> -cf - --exclude .metaxotrail . | tar -x -C <full path>` —
`tar -x -C` needs the folder to exist. While the code is under review `cp` or `ln` of a project
file is refused, and `git archive HEAD` copies the last commit, not the change under review.

## Getting a step reviewed

`status` says **who may write** the open review ticket, and that decides what you do:

- **`independent`** — **invoke the `<step-id>-gated` review skill and nothing else.** It carries
  `context: fork`, so Claude Code runs it in its own agent with no conversation history — you do
  not spawn anything, and you hand it nothing. The reviewer reads the run's own records, writes
  its findings to the issues file, appends its own log line and closes its own ticket from inside
  the fork; the hook sees that the close came from a subagent, and a close on this ticket from
  your thread is refused by name. **Do not wrap it in an `Agent` call** — the one thing a wrapper
  adds is a prompt you write, and a reviewer handed its conclusion is where reviews go wrong.
- **`orchestrator`** — this is the round that follows your own fix, and it is yours: carry out
  the plain review skill's method yourself, on your own eyes, under its compensating rules, and
  close it as the closing section of the `-gated` review skill says. A clean orchestrator round does **not** complete
  the step — the pipeline then opens a fresh **independent** round, which only the fork may
  close. Your round is what earns that fresh pair of eyes, not what replaces them.

What the pipeline does with a verdict is set out below, not yours to choose:

- **`0H 0M` from an independent round** — the step completes and the next opens.
- **findings** — `92-fix` opens on the step reviewed, and it is yours. Discharge every HIGH and
  MEDIUM with proof, close it `fixed` as above, and the pipeline reopens the same review as your
  round.
- **a rollback ordered** — the reviewer's close carried `ROLLBACK <step>`; `93-rollback` opens on
  that earlier step and everything built on it loses its credit. A target the reviewer cannot
  reach is not silently narrowed: the run **holds** and asks the operator.

## When the operator has to decide

Some states have no legal move an agent may make, and the pipeline **asks** rather than guessing.
`python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" question <kind> "<what you found>"` holds the
open ticket and prints the legal replies. The kinds are the pipeline's, not yours — `unreachable`
(a rollback target this step cannot reach), `input` (the thing this step works from is wrong),
`unknown` (a review's line could not be read, so only the operator can clear the close), `misopened` (the pipeline cut the wrong ticket), `end` (the
run should stop short of its target) — and a question that has no legal reply in the current state is
refused rather than written. Every legal reply is printed with what it repeats; show them both.

**And two kinds are about the WORK, not the state: `ask` and `observe`.** When the artifact cannot be finished
without a decision that is the operator's — which of two designs of what the user sees or does, what a requirement means, a
figure only they have — do not write the question into the document and close the step around it.
Ask it: `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" question ask "<what you need to know>"`
holds the ticket the same way. Give it options when the decision is a choice — `--option "<label>"`
for each, two to four, each on one line and none twice; for a question in parts, `--part` before each part's options, at most four
parts. Their reply is the key of an option the pipeline printed (`b`, or `1a 2b` for a question in
parts), or `ANSWER <your answer>` in their own words, and it is applied by nothing: read it off
`status` — the line `answered q<n>: …` — and finish the step with it. An answer credits nothing and closes nothing; the ticket is still yours to close through every
check. If the answer raises a second question, ask again.

When you want their **observation or opinion** — what they see on a screen, whether something looks
right — and the work does not wait on it, ask `question observe "<what you want to know>"`, with an
`--option` for each choice if it has choices, in one part. It holds nothing: the step goes on, and
closes, while it waits. They answer by a click on its sheet or in their own words; it has no keys. It stops
waiting at the step's next close, or when you ask a new question — `question` then says so, and you
tell them in the chat before the new box. If the work must wait for their answer, it is a decision: `ask`.

**Ask once, then wait.** While a question waits on them — `status` prints *WAITING ON THE OPERATOR* —
end your turn and write nothing more: no reminder, no *"still waiting"*, no new question. The gate lets
the turn end every time while they are being asked, and `question` asks nothing new meanwhile but `end`.
When they reply, run `status` and drive the run on to its target. **Before you tell them their answer was
recorded, run `status` and see `answered q<n>`**, or the move applied; if it is not there, nothing was
recorded — say so, and show them the same question again.

**How to ask.** They decide from what they read before the sheet: the briefing in the chat
(`${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md`, "Brief before you ask"), with each option's pros, its cons
and what it costs — your recommendation first, saying it is the recommendation. A content question's options are yours:
pass your recommendation as its first `--option`, so its key is `a` — `1a`, `2a`, … in a question in
parts. A state question's options are the moves the pipeline printed, with what each repeats: mark your
recommendation beside its key instead.
**Copy every key exactly as `status` printed it, in its order — never re-letter or reorder the
replies**, or the key they type names on the sheet a reply the hook does not record. While `status` prints
the lock line, an option that needs a production change says so on its face — *"needs code: <ms> goes
back to its code step"* — and that it repeats the steps the lock line names. Show it on the sheet —
one sheet question per part, headed `q<n>` for a question of one part and `q<n>·<part>` for each part of
a question in parts, each sheet question's text different from the others'. **Each option's label is the option exactly as recorded** — a content question's label, a
state question's plain label, copied exactly as `status` prints it after *on the sheet:* (MetaXoTRail writes it, naming
the step and the milestone, and maps their click back to the move) — with nothing added but *" (Recommended)"* on the recommended one; its key
and a one-line reminder of what it means go in the option's description; the full pros, cons and cost are in the briefing. A state
question of one move gets a second option, *"Talk it over first"*: their click on it is no move, so the question
is asked again under a new `q<n>`, and the run waits while they ask you about it. A state question of more than four moves is not put on the sheet. Tell them to click their
choice, or type the key: the hook records their click in the default, acceptEdits and auto permission modes, and the key in every mode —
both only in the run's own window. From another window a whole instruction, `OVERRIDE …` or `ANSWER …`, typed
out, still counts from any window: write it for them to type or paste. A reply under "Other" that is, word for word, an option's label is that option, recorded as
their click. Any other reply under "Other" is recorded as their words — `OTHER <their words>` — and decides nothing:

- **At an observation, their words are their answer**: `status` shows `answered q<n>: ANSWER <their words>`.
- **At a content decision, ask again, at once.** Rewrite their words into a well-formed option — correct
  wording, what it means for the work — and if it has a drawback or cannot be done, say why in the chat
  first. Then a new `question ask` whose options are theirs, rewritten, with the closest option that can be
  done beside it if theirs cannot, and show its sheet **in the same turn**, saying to read the chat for the
  reasons. Only their click on the new box decides; the step stays held until then. If `question ask` is
  refused because the first question is still waiting — their reply was not recorded, as where no click is
  recorded — **do not ask again**: write their words, rewritten, in the chat; they type `ANSWER <those words>`, or a
  key, to the question already waiting.
- **At a state question, never ask a new question.** Their words are no move: the pipeline refuses them and
  asks the same question again under a new `q<n>`. Say in the chat which move their words come closest to,
  and why none fits if none does, then show that question's sheet.

Text they type that is neither a key nor a whole instruction is discussion: answer it in the chat; the
question still waits.

**The operator answers with an instruction, not with "yes".** Show them the menu `status`
prints and tell them the five forms:

- `OVERRIDE ROLLBACK <step>` — they order the rollback to a step the reviewer could not reach,
  or a different one.
- `OVERRIDE CLOSE <ticket>` — they close the ticket they name on their own authority, on the
  counts of its last line; the record says so, and `report` marks it.
- `OVERRIDE OPEN <ticket>` — they void the ticket the pipeline cut and open the one they name,
  from the set the pipeline enumerated.
- `OVERRIDE END` — they end the run short of its target, answering an `end` question. Only then does
  `archive --abandon` run — as your next command: a close after their answer lapses it. Never pass that
  flag on your own word. The `end` question's other reply, `OVERRIDE OPEN <its ticket>`, keeps the run
  going: nothing ends, and you go on with the open step.
- `ANSWER <your answer>` — their answer to a content question. It authorises nothing.

Or their click on the sheet: the hook records the reply its label names, as if they had typed its key. Or
the key of a printed reply — `a`, or `1a 2b` for a question in parts: the hook records it as the
reply it names, so `a` at a state question is the instruction keyed `a`.

An override **names an action rather than agreeing to one**: a reply of *"20"* or *"yes, do it"* —
anything that is neither one of these forms nor a printed key — is not read by anything, nothing is
recorded, and the ticket stays held. An override is applied by
whatever command runs next — `status` is enough — and `report` says what it did; an answer is
shown there, and applied by no one but you.

**Do not stop and wait here.** The gate decides when the turn ends. Where the skill above says
"Stop", that instruction is for standalone use; under the gate, close the ticket or ask the
operator, and continue. Once they are asked, end the turn and wait in silence.
