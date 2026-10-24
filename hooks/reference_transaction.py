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


def main(argv, stdin, stderr):
    said = refusals(argv[0] if argv else "", stdin.read().splitlines())
    if not said:
        return 0
    for line in said:
        stderr.write("MetaXoTRail refused this: %s\n" % line)
    stderr.write("No commit is lost — git cancelled the change, and the branch or tag still points "
                 "where it did. "
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
