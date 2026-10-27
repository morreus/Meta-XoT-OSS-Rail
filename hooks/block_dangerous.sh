#!/usr/bin/env bash
# MetaXoTRail safety guard (PreToolUse / Bash).
# Detects irreversible/destructive shell commands and ASKS you to confirm before they run
# (it does NOT hard-block). The model cannot self-approve an "ask" — it goes to you.
#
# Contract: on a match, print a PreToolUse "ask" decision as JSON on stdout and exit 0.
# No match -> exit 0 with no output (normal permission flow).
set -uo pipefail

INPUT="$(cat)"

CMD="$(printf '%s' "$INPUT" | python3 -c 'import sys,json
try:
    d=json.load(sys.stdin)
    print((d.get("tool_input",{}).get("command") or "").replace(chr(10)," "))
except Exception:
    print("")' 2>/dev/null || true)"

[ -z "$CMD" ] && exit 0

# Normalise before matching. Matching the raw text misses two whole classes of command:
#   * `git -C <dir> reset --hard` — the optional-global-flag prefix could not span `-C <path>`
#     because the path is a non-dash token, so a common flag like `-C` would hide every git rule.
#   * `"rm" -rf x` and `/bin/rm -rf x` — quotes and a leading path defeated the `rm` anchor.
# Strip quotes, collapse `git -C <dir>` and `git --git-dir=... --work-tree=...` to bare `git`,
# and reduce absolute command paths to their basename. Matching then sees a canonical form.
NORM="$(printf '%s' "$CMD" | tr -d "\047\"" \
  | sed -E "s#(^|[[:space:];&|(])/([[:alnum:]_./-]*/)?(rm|git|find|dd|shred)([[:space:]])#\1\3\4#g" \
  | sed -E "s#\bgit([[:space:]]+(-C[[:space:]]+[^[:space:]]+|--git-dir=[^[:space:]]+|--work-tree=[^[:space:]]+|-c[[:space:]]+[^[:space:]]+))+#git#g")"
CMD="$NORM"

ask() {
  python3 -c 'import json, sys
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": sys.argv[1]}}))' "MetaXoTRail safety guard: $1 — confirm before proceeding?"
  exit 0
}

# --- Irreversible / history-rewriting git ---
echo "$CMD" | grep -Eq 'git([[:space:]]+-[^[:space:]]+)*[[:space:]]+reset[[:space:]]+(--hard|--keep)' && ask "git reset --hard throws away changes you have not committed; git reset --keep can move the branch back past commits"
if echo "$CMD" | grep -Eq 'git[[:space:]]+push' && echo "$CMD" | grep -Eq '(--force([[:space:]]|=|$)|(^|[[:space:]])-f([[:space:]]|$)|[[:space:]]\+[^[:space:]-])'; then ask "a forced git push can overwrite commits on the server that others may have (--force-with-lease is the safer form)"; fi
echo "$CMD" | grep -Eq 'git[[:space:]]+commit[[:space:]].*--amend' && ask "git commit --amend rewrites the last commit"
echo "$CMD" | grep -Eq 'git[[:space:]]+rebase' && ask "git rebase rewrites history"
echo "$CMD" | grep -Eq 'git[[:space:]]+clean[[:space:]]+-[a-zA-Z]*f' && ask "git clean -f permanently deletes untracked files"
echo "$CMD" | grep -Eq 'git[[:space:]]+branch[[:space:]]+-[a-zA-Z]*D' && ask "git branch -D force-deletes a branch"
echo "$CMD" | grep -Eq 'git[[:space:]]+gc([[:space:]]|$)' && ask "git gc can permanently delete old commits that no branch keeps"
echo "$CMD" | grep -Eq 'git([[:space:]]+-[^[:space:]]+)*[[:space:]]+checkout([[:space:]]+[^[:space:]]+)*[[:space:]]+(--([[:space:]]|$)|\.([[:space:]]|$)|\*([[:space:]]|$))' && ask "this git checkout throws away changes to files that are not committed"

# git restore discards the working tree by default; only --staged (unstage) is safe
if echo "$CMD" | grep -Eq 'git([[:space:]]+-[^[:space:]]+)*[[:space:]]+restore([[:space:]]|$)'; then
  if echo "$CMD" | grep -Eq '\-\-staged' && ! echo "$CMD" | grep -Eq '(\-\-worktree|(^|[[:space:]])-[a-zA-Z]*W([[:space:]]|$))'; then
    :
  else
    ask "git restore throws away changes to files that are not committed ('git restore --staged' only unstages)"
  fi
fi

echo "$CMD" | grep -Eq '(^|[[:space:];&|`(])find([[:space:]]|$)' && echo "$CMD" | grep -Eq '[[:space:]]-delete([[:space:]]|$)' && ask "find -delete permanently removes every matching file"

# --- Recursive + force delete (combined OR split OR long flags) ---
if echo "$CMD" | grep -Eq '(^|[[:space:];&|`(])rm([[:space:]]|$)'; then
  if echo "$CMD" | grep -Eq 'rm[[:space:]]+(-[a-zA-Z]*[rR][a-zA-Z]*[fF]|-[a-zA-Z]*[fF][a-zA-Z]*[rR])' \
     || { echo "$CMD" | grep -Eq 'rm([[:space:]]|[[:space:]][^|;&]*[[:space:]])(-[a-zA-Z]*[rR]|--recursive)([[:space:]]|$)' \
          && echo "$CMD" | grep -Eq 'rm([[:space:]]|[[:space:]][^|;&]*[[:space:]])(-[a-zA-Z]*[fF]|--force)([[:space:]]|$)'; }; then
    ask "rm -rf deletes a folder and everything in it, with no undo"
  fi
  # Recursive WITHOUT force still deletes a whole tree; it only prompts per write-protected
  # file, which for an agent-run command is no protection at all.
  if echo "$CMD" | grep -Eq 'rm[[:space:]]+(-[a-zA-Z]*[rR]|--recursive)([[:space:]]|$)'; then
    ask "rm -r deletes a folder and everything in it"
  fi
fi

exit 0
