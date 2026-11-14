import datetime
import json
import os
import shlex
import subprocess
import sys

PREPARED = "prepared"

ZERO = "0"

GUARDED = ("refs/heads/", "refs/tags/")


def _absent(value):
    return set(value) == {ZERO}


def loses_commits(old, new, run=None):
    if _absent(new):
        return True
    if _absent(old):
        return False
    ask = run or _rev_list
    return bool(ask(old, new))


def _rev_list(old, new):
    try:
        done = subprocess.run(["git", "rev-list", "--max-count=1", "%s..%s" % (new, old)],
                              capture_output=True, text=True)
    except OSError:
        return True
    if done.returncode != 0:
        return True
    return done.stdout.strip()


def _current():
    try:
        done = subprocess.run(["git", "for-each-ref", "--format=%(objectname) %(refname)"]
                              + [prefix.rstrip("/") for prefix in GUARDED], capture_output=True, text=True)
    except OSError:
        return None
    if done.returncode != 0:
        return None
    return dict(reversed(line.split(" ", 1)) for line in done.stdout.splitlines() if " " in line)


def refusals(phase, lines, run=None, now=None):
    if phase != PREPARED:
        return []
    out = []
    known = []
    for line in lines:
        parts = line.split()
        if len(parts) != 3:
            continue
        old, new, ref = parts
        if not ref.startswith(GUARDED):
            continue
        if new.startswith("ref:"):
            continue
        if _absent(old) and not _absent(new):
            if not known:
                known.append((now or _current)())
            if known[0] is None:
                out.append("%s: git could not say where it stands, so whether this loses commits cannot be "
                           "answered" % ref)
                continue
            old = known[0].get(ref) or old
        if old == new and not _absent(new):
            continue
        if loses_commits(old, new, run):
            kind, name = ("branch" if ref.startswith(GUARDED[0]) else "tag"), ref.split("/", 2)[2]
            out.append("deleting %s `%s` (at %s) is refused while a run is live" % (kind, name, old[:8])
                       if _absent(new) else
                       "%s `%s` would move back and leave commits behind (%s -> %s)"
                       % (kind, name, old[:8], new[:8]))
    return out


PERMIT = "git_permit.json"
PERMIT_MAX_AGE = 120


def _permit_path():
    try:
        gitdir = subprocess.run(["git", "rev-parse", "--absolute-git-dir"], capture_output=True, text=True,
                                timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return os.path.join(os.path.dirname(gitdir), ".metaxotrail", PERMIT) if gitdir else None


def _command_of(process):
    try:
        line = subprocess.run(["ps", "-o", "args=", "-p", str(process)], capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return []
    words = line.split()
    return [os.path.basename(words[0])] + words[1:] if words else []


def _approved_words(command):
    try:
        words = shlex.split(str(command or ""))
    except ValueError:
        return None
    return " ".join([os.path.basename(words[0])] + words[1:]).split() if words else None


def _bound_here(path, parent=None, now=None, command_of=None):
    parent = parent if parent is not None else os.getppid()
    try:
        with open(path) as handle:
            permit = json.load(handle)
        at = datetime.datetime.strptime(permit["at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        age = ((now or datetime.datetime.now(datetime.timezone.utc)) - at).total_seconds()
        if permit.get("process") != parent or age <= PERMIT_MAX_AGE:
            return False
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        return False
    approved = _approved_words(permit.get("command"))
    return bool(approved) and (command_of or _command_of)(parent) == approved


def _recent(path, now=None):
    try:
        with open(path) as handle:
            at = datetime.datetime.strptime(json.load(handle)["at"], "%Y-%m-%dT%H:%M:%SZ")
        age = ((now or datetime.datetime.now(datetime.timezone.utc))
               - at.replace(tzinfo=datetime.timezone.utc)).total_seconds()
    except (OSError, ValueError, TypeError, KeyError):
        return False
    return 0 <= age <= PERMIT_MAX_AGE


def permitted(path=None, parent=None, now=None, command_of=None):
    path = path or _permit_path()
    parent = parent if parent is not None else os.getppid()
    try:
        with open(path) as handle:
            permit = json.load(handle)
        at = datetime.datetime.strptime(permit["at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        age = ((now or datetime.datetime.now(datetime.timezone.utc)) - at).total_seconds()
    except (OSError, ValueError, TypeError, KeyError):
        return False
    if not 0 <= age <= PERMIT_MAX_AGE:
        return False
    approved = _approved_words(permit.get("command"))
    if not approved or (command_of or _command_of)(parent) != approved:
        return False
    if permit.get("process") is None:
        try:
            with open(path, "w") as handle:
                json.dump(dict(permit, process=parent), handle, sort_keys=True)
        except OSError:
            return False
        return True
    return permit.get("process") == parent


def main(argv, stdin, stderr):
    said = refusals(argv[0] if argv else "", stdin.read().splitlines())
    if not said or permitted():
        return 0
    for line in said:
        stderr.write("MetaXoTRail refused this: %s\n" % line)
    path = _permit_path()
    late = _bound_here(path)
    if late:
        stderr.write("This is the git command they approved, and it ran past the two minutes their approval covers. It "
                     "may have done part of its work: `git status` and `git log` show where it stands. A new approval "
                     "is needed for the rest.\n")
    elif _recent(path):
        stderr.write("Their approval does not cover this git process: it covers the approved command, run once within "
                     "two minutes. A new approval is needed.\n")
    stderr.write(("This change was cancelled, and the branch or tag it named still points where it did; earlier "
                  "changes of this same command may stand. " if late else
                  "No commit is lost — git cancelled the change, and the branch or tag still points where it did. ") +
                 "If files changed under you, `git status` shows them; to put them back as they were "
                 "at the last commit — this throws away edits you have not committed — run `git "
                 "restore --staged "
                 "--worktree .`. If you meant "
                 "to undo work, `git revert <sha>` "
                 "adds a commit rather than dropping one. To send the run back to an "
                 "earlier step, or to end it, ask Claude in the run's window: it puts the "
                 "choice to you. This guard is on while a run is live.\n")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin, sys.stderr))
