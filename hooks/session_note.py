import json
import os
import sys


def note(project, payload):
    import books as K
    import gate as S
    import pipeline as G
    try:
        if not K.running(project):
            above = S.live_run_above(project)
            if above is None:
                return ""
            return ("A MetaXoTRail run is live above this folder, at %s. The gate refuses every turn in this window, "
                    "which sits below the run's root: restart the session at %s." % (above, above))
        events = K.read_log(project)
        hurt = S._broken(project, events)
    except ValueError as exc:
        hurt = str(exc)
    if hurt:
        return ("A MetaXoTRail run is live here, but its books are broken — %s. Show the operator this; "
                "%s ends the run and says so on the record — if its log can be read; if not, the "
                "operator repairs the log or moves it aside by hand." % (hurt, S.ABANDON))
    owner = S.bound(project)
    if owner is None:
        return ("A MetaXoTRail run is live here, bound to no window, so every turn is refused at its end "
                "until the operator approves `bind` in the window that should run it — ask them before "
                "running it.")
    session = payload.get("session_id")
    if session and session != owner:
        return ("A MetaXoTRail run is live here, bound to another window (%s). This window's turns are "
                "not held, but the run's records stay closed to it until the operator approves `bind` — "
                "ask them before running it; a window cleared with `/clear` is a new one." % owner)
    return "A MetaXoTRail run is live here, bound to this window.\n%s" % G.describe(project, events)


def main(argv, stdin, stdout):
    try:
        payload = json.load(stdin)
        words = note(payload.get("cwd") or os.getcwd(), payload)
    except Exception:
        return 0
    if words:
        stdout.write(words.rstrip() + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin, sys.stdout))
