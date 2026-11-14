import json
import os
import re
import shlex
import sys

import books as K
import scope as S
import reference_transaction as R
import write_block as W

ALLOW, DENY = W.ALLOW, W.DENY

PERMISSION = "authorised.json"

PERMISSION_MAX_AGE = 120

REFUSED = "refused.json"
GUARD_PREFIX = "Run this command? "
RUN_IT, DO_NOT_RUN = "Run it", "Do not run it"
PERMISSIONS_LOG = "permissions.log"
PERMITTED = "allowed on the operator's approval"
ALLOWED = "allowed.json"
ALLOWED_MAX_AGE = 10

BLOCKED_GIT = ("reset", "rebase", "checkout", "switch", "restore", "clean", "stash",
               "rm", "pull")

BLOCKED_FLAGGED = {"commit": ("--amend",),
                   "branch": ("-d", "-D", "--delete"),
                   "tag": ("-d", "--delete"),
                   "reflog": ("expire", "delete"),
                   "gc": ("--prune",)}

_CONFIG_READ_FLAGS = ("--get", "--get-all", "--get-regexp", "--get-urlmatch", "--list", "-l",
                      "--get-color", "--get-colorbool")
_CONFIG_NEUTRAL_FLAGS = ("--global", "--local", "--system", "--worktree", "--bool", "--int",
                         "--bool-or-int", "--path", "--expiry-date", "-z", "--null",
                         "--name-only", "--show-origin", "--show-scope", "--includes",
                         "--no-includes", "--fixed-value", "--all")
_CONFIG_VALUE_FLAGS = ("-f", "--file", "--blob", "--type", "--default", "--value")
_CONFIG_READ_VERBS = ("get", "list")


_RECURSIVE = ("--recursive",)

_GIT_VALUE_FLAGS = ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path",
                    "--super-prefix", "--config-env", "--attr-source")
_GIT_BARE_FLAGS = ("-p", "--paginate", "-P", "--no-pager", "--no-replace-objects", "--bare",
                   "--literal-pathspecs", "--glob-pathspecs", "--noglob-pathspecs",
                   "--icase-pathspecs", "--no-optional-locks", "--no-advice", "--no-lazy-fetch",
                   "--version", "--help", "-h", "-v", "--html-path", "--man-path", "--info-path")


_CONFIG_FLAGS = ("-c", "--config-env")
_CONFIG_ALLOWED = ("user.name", "user.email")


_EXPORTERS = ("export", "declare", "typeset", "set")

SAFE_NAMES = ("TMPDIR", "TZ", "LANG", "LC_ALL")
SET_FLAGS = "eux"
SET_NAMES = ("errexit", "nounset", "pipefail")
NAMING_WORDS = ("pgrep", "which", "man", "whatis", "whereis", "apropos", "type")

_UNKNOWN = object()


GIT_HOOKS = os.path.join(".git", "hooks")
REF_HOOK = "reference-transaction"


def hook_path(project):
    return os.path.join(project, GIT_HOOKS, REF_HOOK)


def install(project):
    real = os.path.abspath(R.__file__)
    python = _quoted(sys.executable)
    log = _quoted(os.path.join(K.address(project), K.LOG))
    here = _quoted(os.path.join(K.FLOW, K.LOG))
    try:
        os.makedirs(os.path.join(project, GIT_HOOKS), exist_ok=True)
        with open(hook_path(project), "w") as handle:
            handle.write('#!/bin/sh\n'
                         '# MetaXoTRail\'s git hook. It does nothing once the plugin is gone; delete it then.\n'
                         '[ -x %s ] && [ -f %s ] || exit 0\n'
                         '[ -e "$(git rev-parse --absolute-git-dir 2>/dev/null)"/../%s ] || '
                         '[ -e %s ] || exit 0\n'
                         'exec %s %s "$@"\n' % (python, _quoted(real), here, log, python, _quoted(real)))
        os.chmod(hook_path(project), 0o755)
    except OSError:
        return None
    return hook_path(project)


def _quoted(path):
    return "'%s'" % path.replace("'", "'\\''")


def permission_path(project):
    return os.path.join(K.address(home(project) or project), PERMISSION)


def _in_project(target, project, here=None):
    return W._inside(W._located(target, here or project), project)


def _recursive(words):
    for word in words:
        if word in _RECURSIVE:
            return True
        if word.startswith("-") and not word.startswith("--") and (
                "r" in word or "R" in word):
            return True
    return False


def _git_verb(words):
    rest = list(words[1:])
    while rest:
        word = rest[0]
        if not word.startswith("-"):
            return word
        if word.startswith("--") and "=" in word:
            if _opaque_config(*word.split("=", 1)):
                return _UNKNOWN
            if word.split("=", 1)[0] not in _GIT_VALUE_FLAGS + _GIT_BARE_FLAGS:
                return _UNKNOWN
            rest.pop(0)
        elif word in _GIT_VALUE_FLAGS:
            if _opaque_config(word, rest[1] if len(rest) > 1 else ""):
                return _UNKNOWN
            rest = rest[2:]
        elif word in _GIT_BARE_FLAGS:
            rest.pop(0)
        else:
            return _UNKNOWN
    return None


def _opaque_config(word, value):
    if word not in _CONFIG_FLAGS:
        return False
    return (value or "").split("=", 1)[0].strip().lower() not in _CONFIG_ALLOWED


def _git_refusal(words, prefix=(), exported=False):
    if exported or [word for word in prefix if "=" in word and not word.startswith("-")
                    and word.split("=", 1)[0] not in SAFE_NAMES]:
        return ("this `git` command is run with something set in its environment, and the "
                "environment is one of the places git reads its configuration from — including "
                "`core.hooksPath`, which turns off the hook that refuses destructive updates, and "
                "the aliases that decide which subcommand actually runs. What it would do cannot "
                "be worked out from the command line")
    verb = _git_verb(words)
    if verb == "config" and not _config_reads(words[words.index("config") + 1:]):
        return ("`git config` WRITES the file that decides what git does next — including "
                "`core.hooksPath`, which turns off the hook that refuses destructive updates, "
                "and the aliases that decide which subcommand a later command actually runs")
    if verb is _UNKNOWN:
        return ("this `git` command carries an option before its subcommand that this hook does "
                "not model, so which subcommand it runs cannot be worked out — and a command that "
                "cannot be identified is not run")
    if verb in BLOCKED_GIT:
        return ("`git %s` can discard work or move a branch backwards, and the verb is refused "
                "WHOLE — its read-only forms with it — because telling those apart means reading "
                "flags, which this hook does not do" % verb)
    flags = BLOCKED_FLAGGED.get(verb)
    if flags and [word for word in words[2:]
                  if word in flags or word.split("=", 1)[0] in flags]:
        return "`git %s` with %s rewrites or deletes what is already recorded" % (
            verb, " or ".join(flags))
    return None


def _config_reads(rest):
    rest = list(rest)
    if rest and rest[0] in _CONFIG_READ_VERBS:
        return True
    read, keys = False, []
    while rest:
        word = rest.pop(0)
        if word == "--":
            keys.extend(rest)
            break
        if not word.startswith("-"):
            keys.append(word)
            continue
        if keys:
            return False
        name = word.split("=", 1)[0]
        if name in _CONFIG_READ_FLAGS:
            read = True
        elif name in _CONFIG_VALUE_FLAGS:
            if "=" not in word and rest:
                rest.pop(0)
        elif name not in _CONFIG_NEUTRAL_FLAGS:
            return False
    return read or (len(keys) <= 1 and all("." in key for key in keys))


def _rm_refusal(words, project, here=None):
    targets = [word for word in W._arguments(words[1:]) if not word.startswith("-")]
    if _recursive(words):
        return "`rm -r` drops a whole tree"
    if not targets or "{}" in targets:
        return ("this `rm` names no target of its own — what it deletes arrives from a pipe, "
                "`xargs` or `find`, which this hook cannot see")
    if here is None and [t for t in targets if not os.path.isabs(os.path.expanduser(t))]:
        return ("this command moves the shell somewhere this hook cannot work out, so a relative "
                "path after it names a file nobody can identify")
    inside = [t for t in targets if _in_project(t, project, here)]
    if inside:
        return "`rm %s` deletes work inside the project" % inside[0]
    return None


def _refusal(command, project, anywhere=True):
    try:
        segments = W._segments(command)
    except W.Unreadable as exc:
        return "this command cannot be read as shell (%s), so nothing in it can be judged" % exc
    here, pushed, exported = project, [], False
    for segment in segments:
        moved = W._destination(segment, here, pushed)
        if moved is not W._NOT_A_MOVE:
            here, pushed = moved
            continue
        words = W._command_words(segment)
        prefix = segment[:len(segment) - len(words)]
        if words and os.path.basename(words[0]) in NAMING_WORDS:
            continue
        why = _pipeline_refusal(words, project)
        if why:
            return why
        for index in range(len(words)) if anywhere else (0,):
            verb = os.path.basename(words[index])
            why = (_git_refusal(words[index:], prefix + words[:index], exported)
                   if verb == "git"
                   else _rm_refusal(words[index:], project, here) if verb == "rm"
                   else None)
            if why:
                return why
        if words and words[0] in _EXPORTERS and not _harmless_export(words):
            exported = True
    return None


def _scratch_only(command, project, scratch):
    if not scratch or not _trusted_scratch(scratch, project):
        return False
    root = os.path.realpath(scratch)
    try:
        segments = W._segments(command)
    except W.Unreadable:
        return False
    if not segments:
        return False
    for segment in segments:
        words = W._command_words(segment)
        if not words or words != list(segment) or os.path.basename(words[0]) != "rm":
            return False
        given = W._arguments(words[1:])
        options = [word for word in given if word[:1] == "-"]
        named = [word for word in given if word[:1] != "-"]
        if not named or any(not RM_OPTIONS.match(word) for word in options) or given[:len(options)] != options:
            return False
        for target in named:
            if W._expanded(target) or target.startswith("~") or "{" in target:
                return False
            real = os.path.realpath(os.path.join(project, target))
            if not real.startswith(root + os.sep):
                return False
    return True


RM_OPTIONS = re.compile(r"^-[rRfvd]+$")
SCRATCH_SHAPE = re.compile(r"/claude-[0-9]+/[^/]+/[^/]+/scratchpad$")


def _temp_tops():
    import tempfile
    return {os.path.realpath(top) for top in ("/tmp", "/private/tmp", tempfile.gettempdir())}


def _linked_below_temp(scratch):
    tops = _temp_tops()
    path = scratch.rstrip("/")
    while path and path != os.path.dirname(path) and os.path.realpath(path) not in tops:
        if os.path.islink(path):
            return True
        path = os.path.dirname(path)
    return False


def _trusted_scratch(scratch, project):
    real = os.path.realpath(scratch)
    if (_linked_below_temp(scratch) or not SCRATCH_SHAPE.search(real)
            or not any(real.startswith(top + os.sep) for top in _temp_tops())):
        return False
    root = os.path.realpath(scratch)
    for held in {os.path.realpath(project), os.path.realpath(home(project) or project)}:
        if held == root or held.startswith(root + os.sep):
            return False
    return True


def _pipeline_refusal(words, project):
    import pipeline as G
    act = G.guarded_act(words)
    if act == "anchor":
        return ("`pipeline.py anchor` moves the head mirrored outside the project, which the records are checked "
                "against")
    if act == "archive --abandon":
        try:
            events = K.read_log(home(project) or project)
        except K.BadBooks:
            return None
        if G._damaged_at_target(home(project) or project, events):
            return ("`archive --abandon` at target, with the records not vouched for, files the run's rows as not "
                    "vouched for")
    return None


def _harmless_export(words):
    if words[0] == "export":
        names = words[1:]
        return bool(names) and all(word.split("=", 1)[0] in SAFE_NAMES for word in names)
    if words[0] != "set" or len(words) < 2:
        return False
    rest = iter(words[1:])
    for word in rest:
        if not word.startswith("-") or len(word) < 2 or not set(word[1:]) <= set(SET_FLAGS + "o"):
            return False
        if "o" in word[1:]:
            if word[1:].count("o") != 1 or not word.endswith("o") or next(rest, None) not in SET_NAMES:
                return False
    return True


def _one_refused_command(text, project):
    stripped = text.strip()
    try:
        segments = W._segments(stripped)
    except W.Unreadable:
        return None
    if len(segments) != 1:
        return None
    return stripped if _refusal(stripped, project, anywhere=False) else None


def home(project):
    try:
        if K.running(project):
            return project
    except K.BadBooks:
        return project
    return S.above(project)


def live(project):
    return home(project) is not None


def judge(command, project, payload, clock=None):
    if not live(project):
        return (ALLOW, "")
    if _scratch_only(command, project, (payload or {}).get("scratchpad_dir")):
        return (ALLOW, "")
    why = _refusal(command, project)
    if why is None:
        return (ALLOW, "")
    if _unmatched_git(command):
        return (DENY, "%s, and the agent may not do that. **If undoing is what you want, use `git revert <sha>`.** If "
                      "it really must be this command, run it bare first — %s — so that their approval can reach git's "
                      "own hook; the refusal of the bare command says how to ask them." % (why, UNMATCHED))
    if _permitted(command, project, clock or W._now, note=True):
        return (ALLOW, PERMITTED)
    typeable = _one_refused_command(command, project)
    sheet = bool(typeable) and (payload or {}).get("permission_mode") in W.CLICK_MODES \
        and not (payload or {}).get("agent_id") and S.ours(home(project) or project, payload or {})
    if sheet:
        _store_refusal(project, typeable, clock or W._now)
    return (DENY, "%s, and the agent may not do that. **If undoing is what you want, use `git "
                  "revert <sha>` — it adds a commit rather than dropping one, so the records stay "
                  "true and nothing this run was credited for disappears.** If it really must be "
                  "this command, ask the operator: %s%s"
            % (why, ("on a sheet, or they type it into the chat on its own; it counts once, within two minutes. "
                     "**The sheet:** first a message of its own, with no tool call, saying what the command does, "
                     "why it is needed and your recommendation, ending the turn; then a sheet headed `guard`, its "
                     "question exactly `%s<the command>`, options `%s` — its description what it does and why — and "
                     "`%s`." % (GUARD_PREFIX, RUN_IT, DO_NOT_RUN)) if sheet else
               "they type it into the chat on its own; it counts once, within two minutes.%s" % (
                   " Run it on its own, not inside a longer line." if not typeable else ""),
               "\n    " + typeable if typeable else
               " Tell the operator to type the command ITSELF, without the wrapper around it — a wrapped "
               "command is not one the hook that reads their messages recognises."))


def authorise(payload, project, clock):
    command = (payload.get("prompt") or "").strip()
    if _one_refused_command(command, project) != command:
        return None
    try:
        with open(permission_path(project), "w") as handle:
            json.dump({"command": command, "at": clock(), "source": "typed"}, handle, sort_keys=True)
    except OSError:
        return None
    return command


def overruled(command, project, clock=None):
    if not _permitted(command, project, clock or W._now):
        return ""
    return (" **You did allow this command, and it is still refused**: it would change the run's "
            "records or the plugin's own files, which your permission does not reach. The run's records "
            "and the hook scripts are never written by an agent, whoever asks. Your authorisation "
            "has been used up. If you want to end the run, ask Claude to end it; it will ask you to "
            "confirm.")


def _recorded(project):
    try:
        with open(permission_path(project)) as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def _permitted(command, project, clock, note=False):
    record = _recorded(project)
    if not isinstance(record, dict) or record.get("command") != command.strip():
        return None
    try:
        if W._age(record.get("at", ""), clock()) > PERMISSION_MAX_AGE:
            return None
    except (TypeError, ValueError):
        return None
    if note:
        _note_allowed(project, record, clock)
    _spend(project)
    return record


def _books(project):
    return K.address(home(project) or project)


def _write_json(path, data):
    try:
        with open(path, "w") as handle:
            json.dump(data, handle, sort_keys=True)
    except OSError:
        return None
    return data


def _read_json(path):
    try:
        with open(path) as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _store_refusal(project, command, clock):
    _write_json(os.path.join(_books(project), REFUSED), {"command": command, "at": clock(), "briefed": False})


def stored_refusal(project):
    return _read_json(os.path.join(_books(project), REFUSED))


def clear_refusal(project):
    try:
        os.remove(os.path.join(_books(project), REFUSED))
    except OSError:
        return False
    return True


def record_click(project, command, clock):
    clear_refusal(project)
    return _write_json(permission_path(project), {"command": command, "at": clock(), "source": "click"})


def _verbs(command):
    try:
        return [os.path.basename(word) for segment in W._segments(command)
                for word in W._command_words(segment)[:1]]
    except W.Unreadable:
        return []


UNMATCHED = ("`git` as its first word, written only with letters, digits, spaces, quotes and `- _ . / : @ ^ ~ = + , % { }`, "
             "with no word starting with `~` or `=`, no `=~` or `:~`, and no braces holding `,` or `..`; for a message "
             "with other letters, write it to a file and use `-F <file>`")
PLAIN = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_./:@^~=+,%{}\"'")
NO_REF_MOVES = ("restore", "clean", "rm", "stash")
def _makes_branch(words):
    for word in words[2:]:
        if word == "--":
            return False
        if word.startswith("-") and not word.startswith("--") and ("b" in word[1:] or "B" in word[1:]):
            return True
    return False


def _unmatched_git(command):
    command = command.strip()
    try:
        if len(W._segments(command)) != 1 or "git" not in _verbs(command):
            return False
        words = shlex.split(command)
    except (W.Unreadable, ValueError):
        return True
    if not words or os.path.basename(words[0]) != "git":
        return True
    subcommand = _git_verb(words)
    if subcommand in NO_REF_MOVES or (subcommand == "checkout" and not _makes_branch(words)):
        return False
    return (not set(command) <= PLAIN or any(word.startswith(("~", "=")) or "=~" in word or ":~" in word
                                            for word in words)
            or any("{" in word and ("," in word or ".." in word) for word in words))


def _note_allowed(project, record, clock):
    books = _books(project)
    now = clock()
    _write_json(os.path.join(books, ALLOWED), {"command": record.get("command"), "at": now})
    if "git" in _verbs(record.get("command") or ""):
        _write_json(os.path.join(books, R.PERMIT), {"at": now, "process": None, "command": record.get("command")})
    try:
        run = K.read_log(home(project) or project)[0]["run_hash"]
        with open(os.path.join(books, PERMISSIONS_LOG), "a") as handle:
            handle.write(json.dumps({"run": run, "at": now, "command": record.get("command"),
                                     "source": record.get("source") or "typed"}, sort_keys=True) + "\n")
    except (OSError, K.BadBooks, IndexError, KeyError):
        pass


def approvals(project):
    return [line for line in records(project) if line.get("source") in ("click", "typed")]


def records(project):
    try:
        run = K.read_log(project)[0]["run_hash"]
        with open(os.path.join(K.address(project), PERMISSIONS_LOG)) as handle:
            raw = [line for line in handle if line.strip()]
    except (OSError, ValueError, K.BadBooks, IndexError, KeyError):
        return []
    lines = []
    for line in raw:
        try:
            lines.append(json.loads(line))
        except ValueError:
            continue
    return [line for line in lines if isinstance(line, dict) and line.get("run") == run]


def settled(payload, now=None):
    command = (payload.get("tool_input") or {}).get("command", "")
    project = payload.get("cwd") or os.getcwd()
    if _scratch_only(command, project, payload.get("scratchpad_dir")):
        return True
    books = _books(project)
    for name, limit in ((PERMISSION, PERMISSION_MAX_AGE), (ALLOWED, ALLOWED_MAX_AGE)):
        record = _read_json(os.path.join(books, name))
        if not record or record.get("command") != command.strip():
            continue
        try:
            if W._age(record.get("at", ""), (now or W._now)()) <= limit:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _spend(project):
    try:
        os.remove(permission_path(project))
    except OSError:
        return False
    return True


def source_of(name):
    import inspect
    return inspect.getsource(globals()[name])


if __name__ == "__main__" and sys.argv[1:] == ["--settled"]:
    try:
        sys.exit(0 if settled(json.load(sys.stdin)) else 1)
    except Exception:
        sys.exit(1)
