# Changelog

## 1.1.1 — clearer words

The plugin works exactly as in 1.1.0: only texts changed. The README says what the pipeline, a backlog file and
Claude's scratch folder are; how to save your own changes before a run; that the default mode is shown as "Manual"
in newer Claude Code; a clearer way out if a guard cannot run; and, for uninstalling, where to type the commands and
how to remove the marketplace too. The privacy policy lists the documents a step writes when used on its own, and
the commit `60-commit` makes. The terms name the **Security and quality** tab. In Claude's instructions: a run never
runs `60-commit`; a review of Claude's own fix happens only outside a run; a finished run is filed by Claude; a code
review inside a run reads its part of the plan from the run; and when there is no run, Claude asks you to type a
command rather than start a run's step. Two places now give Claude the file of a skill it cannot load by name: when
a review orders a rollback, Claude reads the rollback method itself, so its rules for redoing the plan are followed;
and `00-ship-lite` says where `00-ship` is. The plugin's details now name its homepage.

## 1.1.0 — questions explained first, approvals by click, every review independent

Questions: before each of the run's questions, Claude explains it in a message of its own, and the list of choices
opens only after that; a turn that ends on a typed question is sent back once to ask it on a list. On a list in
several parts, the parts you clicked stay answered. You can pause the run at any step, a review included.
Commands: a command the guards refuse can now be approved by a click on a list, *Run it*, as well as by typing it;
git's own guard then accepts it too. The guards no longer refuse harmless commands that only mention a risky
word, allow `rm -r` inside Claude's own scratch folder, also check the commands Claude runs in the background,
and refuse everything if they cannot run at all; the README says how to get out. Claude may end its turn
while a background task runs. Records: the run's check of its records is written safely, and a check left behind by
a full disk is told apart from tampering and repaired on your approval. Disk: review copies leave out `.git`,
builds and dependencies; the scratch folder is emptied each time a part is delivered; Claude asks you when free
space falls under 5 GB. The test steps add a stop step for every service a test starts. A rule for Flutter device
builds, and a four-line form for tasks you do by hand.

Reviews: every review round is now done by an independent reviewer, the rounds after a fix too; Claude no longer
checks its own fix between rounds. The test plan is one table for each part of the plan, and its review stops the
run only for a test that cannot be run as written, a rule or a changed behaviour with no test, an important test
that would pass on broken code, or an important test that needs live data or real users' data. The end of a run: if your request named a backlog file, Claude marks what the run
delivered, adds what it left for later, and shows you the change, uncommitted; then it files the run away itself.

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
