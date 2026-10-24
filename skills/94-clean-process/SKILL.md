---
name: 94-clean-process
description: End the current gated run and archive its state, so the pipeline stops interfering with unrelated work in this project. Use when a run is finished, abandoned, or stuck. Documents are kept; only the run's bookkeeping is filed away.
disable-model-invocation: true
argument-hint: (none)
---

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
