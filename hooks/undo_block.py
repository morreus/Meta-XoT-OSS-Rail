import json
import os
import sys

import books as K
import scope as S
import reference_transaction as R
import write_block as W

ALLOW, DENY = W.ALLOW, W.DENY

PERMISSION = "authorised.json"

PERMISSION_MAX_AGE = 120

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
    if exported or [word for word in prefix if "=" in word and not word.startswith("-")]:
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
        for index in range(len(words)) if anywhere else (0,):
            verb = os.path.basename(words[index])
            why = (_git_refusal(words[index:], prefix + words[:index], exported)
                   if verb == "git"
                   else _rm_refusal(words[index:], project, here) if verb == "rm"
                   else None)
            if why:
                return why
        if words and words[0] in _EXPORTERS:
            exported = True
    return None


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
    why = _refusal(command, project)
    if why is None:
        return (ALLOW, "")
    if _permitted(command, project, clock or W._now):
        return (ALLOW, "")
    typeable = _one_refused_command(command, project)
    return (DENY, "%s, and the agent may not do that. **If undoing is what you want, use `git "
                  "revert <sha>` — it adds a commit rather than dropping one, so the records stay "
                  "true and nothing this run was credited for disappears.** If it really must be "
                  "this command, ask the operator to type it into the chat, on its own; it counts once, "
                  "within two minutes.%s"
            % (why, "\n    " + typeable if typeable else
               " Tell the operator to type the command ITSELF, without the wrapper around it — a wrapped "
               "command is not one the hook that reads their messages recognises."))


def authorise(payload, project, clock):
    command = (payload.get("prompt") or "").strip()
    if _one_refused_command(command, project) != command:
        return None
    try:
        with open(permission_path(project), "w") as handle:
            json.dump({"command": command, "at": clock()}, handle, sort_keys=True)
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


def _permitted(command, project, clock):
    record = _recorded(project)
    if not isinstance(record, dict) or record.get("command") != command.strip():
        return False
    try:
        if W._age(record.get("at", ""), clock()) > PERMISSION_MAX_AGE:
            return False
    except (TypeError, ValueError):
        return False
    _spend(project)
    return True


def _spend(project):
    try:
        os.remove(permission_path(project))
    except OSError:
        return False
    return True


def source_of(name):
    import inspect
    return inspect.getsource(globals()[name])
