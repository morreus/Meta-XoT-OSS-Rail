import json
import os
import re
import subprocess
import sys

import books as K
import chain as C
import floor as F
import position as P
import scope as S
import write_block as W

ALLOW, BLOCK, INERT = "allow", "block", "inert"

SESSION = "session"

ABANDON = "`question end`, then `archive --abandon` on the operator's `OVERRIDE END`,"


class BadBind(ValueError):
    pass


def session_path(project):
    return os.path.join(K.address(project), SESSION)


def bound(project):
    try:
        with open(session_path(project)) as handle:
            lines = [line.split()[0] for line in handle.read().splitlines() if line.split()]
    except (OSError, ValueError):
        return None
    return lines[-1] if lines else None


def session_at_the_door(project, clock):
    record = W.read_marker_record(project, clock)
    if not record:
        return None
    return record.get("session") or None


def attach(project, clock, session=None):
    session = session or session_at_the_door(project, clock)
    if session is None:
        return None
    _write(project, session, clock)
    return session


def bind(project, clock, session=None):
    if not K.running(project):
        raise BadBind("there is no run at %s to bind — `init` makes one" % project)
    session = session or session_at_the_door(project, clock)
    if not session:
        raise BadBind("no session is known: `bind` reads the session from the marker the write "
                      "hook leaves for a `pipeline.py` command, and there is no fresh one. Run "
                      "it from inside the Claude Code session that should own this run")
    _write(project, session, clock)
    return session


def _write(project, session, clock):
    with open(session_path(project), "a") as handle:
        handle.write("%s %s\n" % (session, clock()))


def _broken(project, events):
    hurt = K.damage(project)
    if hurt is not None and not hurt.startswith("anchor behind"):
        return "the records have been altered — %s" % hurt
    try:
        P.open_ticket(events, False)
    except P.BadPosition as exc:
        return "the books cannot be positioned — %s" % exc
    off = C.score_disagreements(events)
    if off:
        return ("a close carries a stored score that the events do not reproduce — the log has "
                "been hand-edited or restored from a backup: %s"
                % off[0])
    return None


def free_stop(events):
    if F.asking(events) is not None:
        return True, ""
    question = F.waiting(events)
    if question is None:
        return False, "no question is waiting on the operator — carry on with the work"
    if question.get("asks") == F.OBSERVE:
        return False, ("%s is an observation, which holds nothing — ask it on a decision box (`question ask`) if "
                       "the run must wait for it, or go on with the work" % question["qid"])
    if F.is_other(F.authority(events)):
        return False, ("the operator replied to %s with words that are none of its options — bring their words back "
                       "on a new `ask` box, rewritten as options, and wait for their click" % question["qid"])
    return False, ("%s offers the operator nothing in the run's present state, so it does not wait — carry on with "
                   "the work" % question["qid"])


def note_briefing(project, events, payload):
    if not S.ours(project, payload) or not str(payload.get("last_assistant_message") or "").strip():
        return None
    import undo_block as U
    stored = U.stored_refusal(project)
    if stored and not stored.get("briefed"):
        U._write_json(os.path.join(K.address(project), U.REFUSED), dict(stored, briefed=True))
    question = F.asking(events)
    if question is None:
        return None
    state = W.sheet_state(project, question["qid"])
    if state is None or state.get("briefed"):
        return state
    return W.write_sheet_state(project, dict(state, briefed=True))


SHEET_BLOCKS = 2


def sheet_wait(project, events, payload):
    question = F.asking(events)
    if (question is None or not F.sheetable(question) or payload.get("permission_mode") not in W.MEASURED_MODES
            or not S.ours(project, payload)):
        return None
    state = W.sheet_state(project, question["qid"])
    if state is None or state.get("shown") or state.get("blocks", 0) >= SHEET_BLOCKS:
        return None
    W.write_sheet_state(project, dict(state, blocks=state.get("blocks", 0) + 1))
    if not state.get("briefed"):
        return ("%s is asked and its sheet has not opened. Write the briefing as a message of its own, with no tool "
                "call — what is to be decided and why, each option's gain and cost, your recommendation, and anything "
                "they must act on — and end the turn there. The turn-end check then sends you on to the sheet."
                % question["qid"])
    return ("%s's briefing is in the chat. Now open its sheet (AskUserQuestion), headed %s as `status` shows it, "
            "with nothing written beside it." % (question["qid"], question["qid"]))


_FENCE = re.compile(r"```.*?```", re.DOTALL)


def guess(payload):
    try:
        if payload.get("stop_hook_active"):
            return None
        text = _FENCE.sub("", str(payload.get("last_assistant_message") or ""))
        lines = [line.strip().strip("*_`>").strip() for line in text.splitlines()]
        lines = [line for line in lines if line]
        if not lines or not lines[-1].endswith("?"):
            return None
        return ("Your message ends with a question and no sheet. Ask it on a multiple-choice sheet "
                "(AskUserQuestion): the explanation stays in the chat, each option's gain and cost in it, and the "
                "sheet holds the choices. If it was not a question to the user, end the turn again.")
    except Exception:
        return None


def credited_commits(events):
    out = []
    for event in events:
        if event.get("kind") == "close" and event.get("commit"):
            out.append((event.get("ms") or "", event.get("ticket", ""), event["commit"]))
    return out


def _is_ancestor(project):
    def ask(sha):
        try:
            done = subprocess.run(["git", "-C", project, "merge-base", "--is-ancestor", sha,
                                   "HEAD"], capture_output=True, text=True)
        except OSError:
            return None
        return done.returncode
    return ask


def lost_commits(project, events, run=None):
    ask = run or _is_ancestor(project)
    out = []
    for milestone, ticket, sha in credited_commits(events):
        answer = ask(sha)
        if answer == 0:
            continue
        out.append("%s's commit %s, credited by %s, is no longer in HEAD's history%s"
                   % (milestone or "a milestone", sha[:8], ticket,
                      "" if answer == 1 else " — and git could not be asked, which is reported "
                                              "rather than passed over"))
    return out


def _report(project, events):
    lost = lost_commits(project, events)
    if not lost:
        return ""
    return ("CREDITED WORK IS MISSING FROM THE HISTORY — reported, not refused:\n  " + "\n  ".join(lost)
            + "\n`git reflog` shows where it went; whether to bring it back is the "
              "operator's call: `git revert` is yours to propose, `git reset` theirs to type.\n")


def live_run_above(project):
    here = os.path.dirname(os.path.abspath(project))
    while True:
        try:
            if K.running(here):
                return here
        except K.BadBooks:
            return here
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent


def running_in_background(payload):
    tasks = payload.get("background_tasks")
    return isinstance(tasks, list) and any(isinstance(task, dict) and task.get("status") == "running"
                                           for task in tasks)


def decide(project, payload):
    try:
        if not K.running(project):
            above = live_run_above(project)
            if above is None:
                if K.rotated(project):
                    return (INERT, "")
            if above is not None:
                return (BLOCK, "there are no books at %s, but a live run sits above it at %s. A "
                               "session started below the project root would end every turn "
                               "unjudged, so this one is refused instead: if the shell moved there, "
                               "`cd %s` goes back; if the session started there, "
                               "restart it at %s. Nothing here has been judged against that run — the "
                               "gate reads the folder it was given and no other."
                        % (project, above, above, above))
            return (ALLOW, "")
    except K.BadBooks as exc:
        return (BLOCK, "the books are broken — %s. %s ends a run whose log can be read — this one "
                       "cannot be, so the operator repairs the log or moves it aside by hand."
                % (exc, ABANDON))
    try:
        events = K.read_log(project)
    except (K.BadBooks, ValueError) as exc:
        return (BLOCK, "the books cannot be read — %s. Nothing that cannot be read is allowed; "
                       "%s ends a run whose log can be read — this one cannot be, so the operator "
                       "repairs the log or moves it aside by hand." % (exc, ABANDON))
    try:
        note_briefing(project, events, payload)
    except (K.BadBooks, ValueError):
        pass
    hurt = _broken(project, events)
    import pipeline as G
    if hurt:
        if G._damaged_at_target(project, events):
            return (BLOCK, "%s. A run whose books are broken never lets a turn end; %s" % (hurt, G._target_ways_out(project)))
        return (BLOCK, "%s. A run whose books are broken never lets a turn end; %s ends the run and "
                       "says so on the record." % (hurt, ABANDON))
    owner = bound(project)
    if owner is None:
        return (BLOCK, "this run is bound to no session — it was started outside a Claude Code "
                       "session, or the binding was lost — so it blocks in every window until "
                       "`pipeline.py bind` (its full command is in the `00-ship` skill) is run, "
                       "with the operator's approval, from the session that should own it.")
    session = payload.get("session_id")
    if session and session != owner:
        return (INERT, "")
    report = _report(project, events)
    free, why = free_stop(events)
    if free:
        held = sheet_wait(project, events, payload)
        if held:
            return (BLOCK, held)
        return (ALLOW, report)
    if G._damaged_at_target(project, events):
        return (BLOCK, "%s%s" % (report, G._target_ways_out(project)))
    if C.score(events) == C.target(C.chain_of(events)):
        return (BLOCK, "%sThe run is at its target. Before it is filed, %s; then `pipeline.py archive` ends the run, "
                       "and the gate stops holding." % (report, G.filing_words()))
    if running_in_background(payload):
        return (ALLOW, report)
    return (BLOCK, "%s%sThe run is not finished. %s\n%s"
            % (report, why + "\n",
               "Close the open ticket, or ask the operator with `question`.",
               G.describe(project, events)))


def main(argv, stdin, stdout, stderr):
    try:
        payload = json.loads(stdin.read() or "")
        if not isinstance(payload, dict):
            raise ValueError("the payload is JSON but not an object: %r" % (payload,))
    except ValueError as exc:
        stderr.write("the gate could not read its payload (%s) and refuses the turn rather than "
                     "let it end unjudged\n" % exc)
        return 2
    project = payload.get("cwd") or os.getcwd()
    try:
        verdict, words = decide(project, payload)
    except Exception as exc:
        stderr.write("the gate failed and refuses the turn rather than let it end unjudged: "
                     "%s: %s\n" % (type(exc).__name__, str(exc).strip().splitlines()[-1]
                                   if str(exc).strip() else ""))
        return 2
    if verdict == BLOCK:
        stderr.write(words.rstrip() + "\n")
        return 2
    sent_back = None
    try:
        if not (K.running(project) and F.asking(K.read_log(project)) is not None):
            sent_back = guess(payload)
    except Exception:
        sent_back = None
    if sent_back:
        stderr.write(sent_back + "\n")
        return 2
    if verdict == ALLOW and words:
        stderr.write(words.rstrip() + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin, sys.stdout, sys.stderr))
