---
name: 40-test-plan-gated
description: GATED 40-test-plan — the /00-ship* variant, for use ONLY while a run is active. Invoke the plain /40-test-plan when there is no run. Plans the tests from the study, the plan and the code that was built. It covers normal, unusual and error cases, gives each test a measurable pass rule, and puts the riskiest first. Use it after /30-implement-plan, before /50-test-impl.
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

## One milestone at a time — and a milestone may honestly have nothing to test

The test stages are counted per milestone: this plan covers **the milestone you were given**, not
the whole feature. The release-level suite — the cross-cutting matrix, the regression sweep, the
end-to-end — belongs to the plan's **highest-numbered milestone**, the integration one, which is
where defects that only appear *between* milestones are found. **On that milestone this plan IS
the release-level suite**: it builds nothing by design, and the absence of milestone code there is
not a finding and not a gap — plan the end-to-end run across everything the earlier milestones
shipped.

⚠️ **Some milestones have nothing to test, and saying so is a valid plan.** An assumption-validation
milestone's deliverable is the measurements themselves; a milestone that only prepares an
environment has no behaviour of its own. Write that, name why, and say what evidence stands in
place of tests. Do **not** invent scenarios to fill the section — hollow tests are worse than an
honest absence, because they pass. The reviewer at `41-review-test-plan` checks the claim, so it is
a statement on the record, not a way out.

ultrathink: Create a comprehensive, evidence-based test plan for: $ARGUMENTS

## Prerequisites
- `WORKING.md` holds the map and the plan, with completed milestone(s); there is an implementation to test (or this is the highest-numbered milestone — see above).
- Read NOW: the context map (scope, **Project-Risk Touchpoints**, assumptions), the plan (Scale & Edge Cases, risks), the **actual diff** (`git diff` / `git diff --staged`, plus `git status --porcelain --untracked-files=all` and every new file, read in full), existing test patterns in the repo (grep for test files), and `${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md` + `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md` (the project's test commands + risk checklist).

**If the implementation is missing → STOP. Implement first (`/30-implement-plan`).**

---

## PHASE 1: Scenario discovery (every test must trace to a source)
- **From the context map** — entry points, data/state flows, Project-Risk Touchpoints.
- **From the plan** — assumptions to validate, the Scale & Edge Cases table, the risk list.
- **From the implementation** (read the diff) — public APIs changed, conditional branches, error paths, and the **stack-specific concerns from `stack_rules/<stack>.md`** (e.g. Python: dtype/precision, data leaking from the future, idempotency; Unity: lifecycle/serialization/UI; Flutter: async/rebuilds/platform).
- **From the web** (only for non-obvious areas) — common bugs/edge cases for this kind of change.

### Test-type checklist — walk EVERY type; each yields ≥ 1 scenario or is marked N/A with a reason
Forcing yourself through these is how you surface the edge cases the happy path hides:
- **Happy path** — typical valid input.
- **Boundary** — min/max, zero, one, empty, full, off-by-one, first/last element.
- **Invalid / negative** — wrong type, malformed, out-of-range, garbage input.
- **Null / empty / missing** — null, empty collection, absent field, defaults only.
- **Error & failure paths** — exceptions, timeouts, retries, partial failure, rollback/cleanup.
- **Idempotency / reproducibility** — run it twice; same input → same output (byte-identical for artifacts).
- **State & ordering** — repeated calls, out-of-order events, stale state, resume-after-interrupt.
- **Concurrency** — parallel access, races, locking, double-processing.
- **Scale / performance** — large inputs, memory, throughput, behaviour under load/timeouts.
- **Data integrity / precision** — dtype, rounding, very large/small numbers, encoding, truncation.
- **Time & timezone** — boundaries, DST, ordering, future/past dates.
- **External dependencies** — API errors, rate limits, network loss (mocked / dry-run — never live).
- **Security / secrets** — injection, authorization, and no secret/`.env` leakage in logs or output.
- **Regression** — pre-existing behaviour still holds.

Then add any **stack-specific types** from `stack_rules/<stack>.md` (e.g. Python: data leaking from the future in time-series; Unity: serialization/scene-reference breakage; Flutter: rebuild correctness).

---

## PHASE 2: Test plan output → `WORKING.md`

**Write it INTO the working document**, below the plan — the map, the plan and the test plan are
one document. Never open the file by overwriting.

Required sections: What is tested · What is not tested · How to run it

Those three headings, exactly, are required, and inside a run they are checked for; write them as headings. The
scenarios, the coverage matrix and the prioritisation go under **What is tested**; the exclusions
and the honest *nothing to test* case under **What is not tested**; the commands, fixtures and
preconditions under **How to run it**.

**Categories — use the ones the stack actually has** (from `stack_rules/<stack>.md`), e.g.:
- **Automated** (unit/integration) in the project's framework (`pytest` / Unity Test Framework / `flutter test`).
- **Reproducibility / determinism** — same input → same output / byte-identical artifact (data & pipelines).
- **Manual / device / UI** — where human judgment or a device is needed (UI stacks: verify ≥ 2 aspect ratios).
- **Regression** — existing behaviour still works.

**Coverage matrix** — areas × test type.

**Per scenario** (T001, T002, …):
| Field | Content |
|-------|---------|
| ID / Name | T0NN / descriptive |
| Source | context map / plan / code / web |
| Priority | P0 (critical) … P3 (low) |
| Preconditions | required state/data — **and how you will arrange it** (see below) |
| Steps | action → expected observable result |
| Acceptance criteria | **measurable, pass/fail** — no "works correctly"; include perf/data thresholds where relevant |
| Edge cases | null/empty/boundary/failure/concurrency |
| Evidence | output / log excerpt / screenshot / metrics |

**Every precondition must be one you can ARRANGE.** For each scenario, say how its starting state
comes about: a fixture, an emulator or test instance, a seeded local database, a mock. "Production
happens to be in this state" is not an answer, and neither is waiting for it to become so.

This is not pedantry about wording. A plan whose preconditions depend on live state is not merely
unrunnable — it quietly pressures whoever runs it to *create* that state, and the states worth
testing are exactly the destructive ones: an empty queue, a deleted record, a failed payment.

If a scenario genuinely needs a state you cannot arrange safely, that is a finding about the TEST
ENVIRONMENT, and it belongs in the plan now: name what is needed (emulator, seeded instance,
fixture) as a prerequisite, or mark the scenario BLOCKED here with the reason — do not write it as
though it will run and leave the discovery to the person executing it.

**Risk-based prioritization** — map the highest-impact risks (and each Project-Risk Touchpoint) to the tests that cover them.

**Definition of Done** — all P0 pass; P1 pass on primary targets; no new errors/warnings; evidence collected.

**Excluded from testing** — list with justification (out of scope / covered elsewhere / risk accepted).

---

## PHASE 3: Test-quality self-check (challenge your own plan)
- Does every changed code path / branch have at least one test?
- Are acceptance criteria pass/fail and objective — not "looks right"?
- **Could the feature be broken and a test still pass?** (too-easy tests — fix them.)
- Is every Project-Risk Touchpoint covered by a test?
- Are edge cases and error paths covered, not just the happy path?
- Can every precondition actually be arranged? (see PHASE 2 — this is the one that gets skipped.)

**Then read the findings the earlier milestones' reviews raised, and check this draft against
what they already found.** Same-shaped artifacts collect same-shaped findings —
live-production preconditions, unfalsifiable acceptance bars, evidence lines that did not match the
step that produced them.

Do this AT THE END, as a check, not at the start as a template. Reading the prior milestone first
anchors you to its shape, and the point of a fresh plan is to notice what that one missed. Read
your draft, then read the findings, then look again at your draft.

Only the earlier milestones **of this work** — that is history the reviewers wrote down and you can
verify. Do not import "lessons" from elsewhere in the conversation.

---

## RULES
1. **Evidence-based** — every test traces to context map / plan / code / web.
2. **Measurable acceptance criteria only** — no vague "works".
3. **Categorize honestly** — don't mark a human-judgment test as automated.
4. **Prioritize by risk** — P0 covers the highest-impact scenarios.
5. **No live/irreversible actions in tests** — for production or money-moving code (e.g. anything in the context map's Project-Risk Touchpoints), tests use dry-run / sandbox accounts / fixtures, never real payments, orders or production writes.

Stop after creating the test plan. Do not execute tests.

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
