# Changelog

## 1.0.1 — a clearer start for newcomers

Only the README changed; the plugin works exactly as in 1.0.0. "What you need" now says, in plain words, what
Claude Code, Python and Git are, and that you can ask Claude Code to set up Python and Git for you. "A first run"
starts with talking your idea through with Claude, then typing the command. "Install" says how to start a new
session after installing: type `/exit`, then `claude`.

## 1.0.0 — first public release

The first public release of Meta-XoT-OSS-Rail: the full and the short chain, each step on its own, and the hooks
that enforce the process. You answer business questions; when the work needs a development stack your project does
not have, Claude asks you once to choose from up to three options, and sets it up before building. Before every
question, Claude explains in the chat what you are deciding; each question the pipeline asks ends with a reminder
to Claude to explain it to you in the chat first. The README's "Updating" says how to get a new version, and how to
be told of one. It works in Claude Code only: claude.ai and Cowork do not install it — a run on claude.ai's chat
could not be guarded, and Cowork is not tested.
