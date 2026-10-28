---
name: 30-implement-plan-gated
description: GATED 30-implement-plan — the /00-ship* variant, for use ONLY while a run is active. Invoke the plain /30-implement-plan when there is no run. Builds one milestone of the plan and checks it by running it. It stops and asks when something is unclear, and updates the plan's documents. It needs a plan from /20-plan-impl first.
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

Implement milestone $ARGUMENTS from the plan in the working document, `WORKING.md`.

If no argument is given: implement the next unfinished milestone.

---

## PHASE 0: Pre-flight Check (MANDATORY)

- [ ] `WORKING.md` exists and holds the implementation plan. A context map is expected too,
      unless the plan has an *Agreed context* section — what was agreed in conversation, written down — in its place (work that began from an agreed plan) —
      do not stop and demand a map in that case.
- [ ] Target milestone is defined with clear exit criteria
- [ ] No unresolved blockers from previous milestones
- [ ] This is not the plan's **highest-numbered milestone**, when the plan has more than one besides M0. That one builds nothing by design
      and has no implementation to do, so if you were asked to implement it, the plan is wrong
      about it: STOP and say so.

**If any check fails → STOP. Run `/20-plan-impl` first.**

Required sections: none

The artifact of this step is the code — a working tree that changed since the previous
milestone's commit — not headings. Re-read the milestone NOW: files to change, verification steps, exit criteria, assumptions to validate. If stack rules aren't in context, read `${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md` + `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md`.

---

## PHASE 1: Implementation

### Rules — STRICTLY ENFORCE
1. **ONLY this milestone** — no scope creep, no "while I'm here" changes.
2. **No unrelated refactors** — note tech debt in `WORKING.md`, under a *Future work* heading (add it if missing).
3. **Match existing patterns** — grep for similar code first, follow conventions.
4. **Minimal diff** — smallest change that achieves the milestone goal.
5. **Never perform an irreversible/production/money-touching action autonomously** — if the milestone touches anything in the context map's **Project-Risk Touchpoints** (e.g. payments, production data, the project's protected files), STOP and hand back to the user with exactly what you intend to do. Destructive git / `rm -rf` are confirmation-gated regardless.

**Before installing anything outside the project** (M0 setting up a new stack), show the user the full list and wait for one approval (`20-plan-impl`, M0).

### Blocked Check (before AND during implementation)
If you hit: unclear requirements, missing information, unexpected behavior, or an assumption proven wrong → **STOP**.

When blocked:
1. Document the blocker in `WORKING.md` → Unknowns.
2. Describe what you learned and how to unblock.
3. **Ask the user** the specific question when it is about what the work should do or a fact only they have. A technical blocker is yours to solve: investigate it, and if it shows the plan was wrong, say so in the step's record, so the review sends the work back to the plan. In a run, if nothing could be built, say so with `question input`, so the operator can send the work back to the plan.
4. Output: `BLOCKED: [reason]`. Do not fabricate success or work around it.

### Instrumentation (only if needed to verify)
Add debug logging when the milestone can't be verified confidently or an assumption needs runtime validation. Use **the stack's instrumentation style from `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md`**:
- Python: `logging` gated by a `--debug` flag/env — not bare `print()` spam.
- Unity: `Debug.Log` under `#if UNITY_EDITOR || DEVELOPMENT_BUILD`.
- Flutter: `debugPrint` / `assert` under `kDebugMode`.
Low-noise, event-based. Mark it clearly removable; gate or remove before commit.

---

## PHASE 2: Self-Verification (MANDATORY)

### Code Verification
- [ ] Compiles / imports cleanly; no new warnings
- [ ] Linting/formatting passes (if the project uses it)

### Behavior Verification
Run the verification steps from the plan and record ACTUAL results:
| Step | Expected | Actual | Pass? |
|------|----------|--------|-------|
| ... | ... | ... | ✓/✗ |

### Cross-Reference Check
- [ ] Implementation matches the plan spec
- [ ] All planned files changed (no more, no less)
- [ ] Exit criteria met

### Self-review of your own diff
- Re-read your diff **file by file** (don't eyeball the whole thing at once — you lose focus on large changes).
- **Prove behaviour, don't infer it from names**: run the code / test and paste REAL output; don't assume a function works because it's named well.
- **Second pass on edge cases & error paths**: once the happy path passes, deliberately re-check empty/null/boundary inputs and failure handling — that's where the bugs hide.

**If ANY verification fails → fix it, or mark the milestone INCOMPLETE with the reason.**

---

## PHASE 3: Documentation Update (MANDATORY)

Update `WORKING.md` — write into it, and never open it by overwriting:
- **Milestone status:** ✅ DONE / ❌ INCOMPLETE / 🚧 BLOCKED + timestamp + commit hash (if committed) —
  **written under the milestone's own existing heading, never as a new `M<n>` heading.** Every
  `#### M<n>` heading is a milestone, and a second heading for the same number makes its section
  undecidable: *one milestone, one heading*. A status line, a `Log` sub-section, a table row —
  anything but a heading whose first word is the milestone's id.
- **Files this milestone touched** — the explicit list, with what changed in each. ⚠️ **This is the
  reviewer's scope boundary, so it is not optional.** Until earlier milestones are committed, a
  reviewer running `git diff` sees every milestone's work at once and cannot tell yours apart; this
  list is the only thing that separates them. Include files you touched *accidentally* — an SDK
  import that rewrites a dependency manager belongs here even though you did not type it.
- **Instrumentation added:** what it logs, how to trigger, where output appears, how to remove.
- **Discoveries:** anything learned that affects later milestones; assumptions validated/invalidated.
- **Assumptions Ledger:** update validated/invalidated entries.

---

## PHASE 4: Output Summary

**Files Changed:**
| File | Change Type | Lines |
|------|-------------|-------|

**Remaining Assumptions:** | # | Assumption | Status (Validated ✓ / Pending / Invalidated ✗) |

**Verification performed** — per the stack's verification style (from `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md`), e.g.:
- Python: ran the script / `pytest`; pasted real output; sanity-checked data (row counts, dtypes).
- Unity: entered Play mode; tested at ≥ 2 aspect ratios (e.g. 16:9 and 9:16); captured Console/screenshot.
- Flutter: `flutter test` + `flutter analyze`; ran on a device at ≥ 2 screen sizes.

**Milestone Status:** ✅ COMPLETE / ❌ INCOMPLETE [what's left] / 🚧 BLOCKED [blocker + how to unblock].

---

## CRITICAL RULES — DO NOT VIOLATE
1. **Never fabricate success** — if verification fails, say so.
2. **Never skip verification** — run the actual steps, report actual results.
3. **Stop when blocked; ask, don't assume** — never work around an unknown; ask the user only what is theirs (the Blocked check above).
4. **One milestone only** — resist "one more thing".
5. **Never perform irreversible/production/money-touching actions autonomously** — hand back to the user.
6. **Code changed = docs updated** — no exceptions.

Stop after Phase 4. Do not proceed to the next milestone without user approval.

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
