---
name: 94-clean-process
description: Ends the current run and files away its records, so the process stops affecting other work in the project. Use it when a run is finished, abandoned or stuck. Your documents are kept.
disable-model-invocation: true
argument-hint: (none)
---
**The rule for questions.** Before any question, first say you are going to ask. Give the context and the content, so the user understands. This is the last thing you write, after all tool calls. Then ask the question on a sheet. In a run, write that briefing as a message of its own, with no tool call, and end the turn there; the turn-end check sends you on to the sheet. End the briefing with a short block — your recommendation, and anything to act on — and put each option's cost in its description on the sheet as well: the sheet opens over the end of a long message. Each option's pros, cons and cost, and your recommendation, come in the briefing; anything to act on is in the chat as plain text, never only on the sheet (`${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md`, "Brief before you ask").


# 94-clean-process — file the run away and let go of the project

Ends the active `/00-ship*` run. After this the turn-end hook is inert here again and you can have
an ordinary conversation in this project without the gate blocking every turn.

## What it does

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" archive              # a finished run
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" archive --abandon    # an unfinished one
```

An unfinished run is **refused** without `--abandon`, and the refusal prints the score it reached
against the chain's target. **`--abandon` is refused too until the operator has answered an `end`
question with `OVERRIDE END`**: ask it with `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pipeline.py" question
end "<what is being dropped, and why>"`, show them the question, and write in the chat the line they paste
to answer it, on its own: `OVERRIDE END`. The whole `OVERRIDE END` line counts from any window; a one-letter answer key only
from the run's own window, and this may not be it. Then wait for their reply. The
abandonment is written on the record, with the score, and stays there.

The run's event log — its own record, `.metaxotrail/events.jsonl` — is **rotated, not
deleted**: it becomes `events.jsonl.1` (then `.2`, and so on) beside the books, so a finished
run's history is kept; a new run adopts from the documents, not from this log. The process log and the
issues file stay where they are and are renamed aside by the next `init`. Nothing is deleted,
which is why this archives rather than removes.

**Your documents are untouched.** `WORKING.md` and `TEST_RESULTS.md` at the project root are
deliverables, not run state. They stay exactly where they are.

**One thing stays that nothing here cleans:** each run leaves one small anchor file in
`~/.claude/metaxotrail-anchor/` — the check the run makes to see whether its records were rebuilt. It is inert once the run
is archived and breaks nothing. Deleting that folder is yours, by hand, after the last run you care
about is archived; no command does it for you, on purpose.

## The backlog — before a finished run is filed, right after an abandoned one

The steps are `00-ship`'s section *Before the run is filed* (`${CLAUDE_PLUGIN_ROOT}/skills/00-ship/SKILL.md`), and
the order matters:

- **A finished run:** update the backlog first, then `archive`.
- **An abandoned run:** `archive --abandon` first, then the backlog, right after it — a run can be ended while a
  review is open, and the backlog file cannot be written until no run is live.

The steps: find the backlog — the file the working document's `Backlog:` line names, or else the file the request
names; if neither names one, there is nothing to do. Mark each delivered item *built in <version>, run <hash>,
commit <sha>*, and say what is left of an item partly done; an abandoned run marks its items *not done* or *partly
done*. Add a row for each `OUT OF SCOPE:` finding of the issues file, naming its run and ticket (`<version>, run
<hash>, <ticket>`) — unless a row already names that same run and ticket, or that same finding, or the run's records
say it was fixed; a ticket alone is not a match, since ticket ids restart in every run. Tell the operator which were
skipped and why. Show them the change, and leave it uncommitted.

## When to use it

- The run finished and you want the project quiet again.
- The run is stuck — the gate keeps blocking and the operator has decided to abandon it.
- You want to start a different piece of work. `init` refuses to start a second run while one is
  live, and this is the sanctioned way to clear it. Do **not** work around the refusal by any
  other route: that is how an unfinished run gets laundered into a clean one.

## Before you run it

If the run was abandoned rather than completed, say so to the operator first, in one line: what
step it reached, what was outstanding, and why it is being dropped. An archived run that nobody
explained is a gap in the record.

## After

Confirm to the operator that the run is ended, where its log went and that the documents were
kept. Then stop.
