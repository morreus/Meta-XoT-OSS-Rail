# Meta-XoT-OSS-Rail

*Vibe coding on rails.*

Meta-XoT-OSS-Rail is a free, open-source plugin for [Claude Code](https://code.claude.com). It turns a
simplified software development process into a game with a score — one number per step, together a
vector — and makes that score the agent's goal. So the agent does not stop at writing the code: it takes
your request through every step of the process to a finished result, without skipping one, and without
you having to set guardrails by hand.

You describe what you want, and it takes the work all the way to the end — study, plan, implement and
test — by itself, pausing only to ask you what is yours to decide: business questions, and risky actions
such as deleting files and folders or overriding the process. It does this through 29 skills (18 commands
you can type, and 11 internal copies a run uses for its steps), 6 hooks and more than 15 code files. Technical decisions are made by the agent, to fit your requirements and needs
— except a development stack the work needs and your project does not have, which Claude proposes in
business terms for you to choose.

Its name, and the start of every command, is `metaxotrail`.

## Contents

- **[What it is](#what-it-is):** [the idea](#the-idea-software-development-as-a-game) ·
  [the score is a vector](#the-score-is-a-vector) · [snapshots](#snapshots-each-review-starts-where-the-last-one-stopped) ·
  [why it works](#why-it-works) · [the name](#the-name)
- **[Why use it](#why-use-it):** [what you get](#what-you-get) ·
  [who it is for](#who-it-is-for-and-the-problems-it-solves) · [what it is built for](#what-it-is-built-for) ·
  [is that all?](#is-that-all)
- **[Getting started](#getting-started):** [what you need](#what-you-need) · [install](#install) ·
  [before your first run](#before-your-first-run) · [a first run](#a-first-run) ·
  [your answers](#your-answers) · [examples](#examples)
- **[How a run works](#how-a-run-works):** [the steps](#the-steps) ·
  [when something goes wrong](#when-something-goes-wrong) · [when the run is finished](#when-the-run-is-finished)
- **[Using the skills on their own](#using-the-skills-on-their-own)**
- **[Reference](#reference):** [the commands](#the-commands) ·
  [what it changes on your machine](#what-it-changes-on-your-machine) · [limits](#limits) ·
  [updating](#updating) · [uninstalling](#uninstalling)
- **[The project](#the-project):** [contributing](#contributing) · [support](#support) · [licence](#licence) ·
  [privacy policy](#privacy-policy) · [terms of use](#terms-of-use)

## What it is

### The idea: software development as a game

A generative model asked to "build this feature" writes whatever looks right to it, and then tells
you it is done. What you get is hard to predict, and what you are told about it is the model's own
opinion.

Meta-XoT-OSS-Rail gives the model a different goal. **The goal is not the feature. The goal is to win
a game, and the only way to win is to follow the software development process to the end.** Building
the feature correctly is what winning looks like.

This is the backbone of the whole design, and it works the way Claude Code's `/goal` command does: the
model keeps working until its goal is met. But the goal set for the model is not "finish this task".
The task is still what the work is for; the goal is to reach the highest possible score in the process
that delivers it. The run ends only when the score reaches its target, or when you choose to end it. The `00-ship` skill also carries a
ready `/goal` line: it names the task, but its finish line is the full score, not the task.

The game is the development process, turned into rules a machine enforces:

| In a game | In Meta-XoT-OSS-Rail |
|---|---|
| The rules, which no player can break | **Hooks**: Claude Code runs them on every command and file write (`Bash`, `Write`, `Edit`, `NotebookEdit`), when you answer, and at the end of every turn, and they refuse the moves the process does not allow (see [Limits](#limits)) |
| The levels, played in order | **The steps**: understand the code, plan, build one part at a time, test it |
| The points | **The score**: a number for each step, which rises as that step and every step after it are completed; a review step completes only when an independent reviewer passes it, or when you accept it: starting from your own notes or plan, or closing it when the pipeline asks you |
| The referee | **A separate reviewer** for every step, running in its own agent, which cannot edit what it reviews |
| The score board, which no player can touch | **The run's records**: the score is kept in a log only the pipeline writes; Claude adds one line per step, which the pipeline checks against the close command Claude ran |
| Winning | **The target score**: every step of every part closed. Until then, Claude is not allowed to end its turn, except while it waits for your answer |

### The score is a vector

The steps are numbered in order, and the score has one number for each. Each number counts how many
steps, from that one to the last, are completed. On the short chain of six steps the target is
`(6, 5, 4, 3, 2, 1)`: every step done. After the map and its review, it reads `(2, 1, 0, 0, 0, 0)`.
With several parts, the later numbers rise part by part, in fractions of a step.

- **It shows where the run stands.** Because each number also counts the steps after it, the vector
  shows at a glance how far the run has come and what is still open.
- **It falls when work goes back.** When a review sends the work back, the steps built on the wrong
  document lose their credit and the numbers drop; they rise again only when that work is done and
  reviewed again.
- **It decides the end.** The run is won when the vector equals the target.

### Snapshots: each review starts where the last one stopped

When a review of a document closes — the map, the plan, the test plan or the test results — the
pipeline keeps a copy of that document as the reviewer saw it, where Claude cannot change it.

- **Documents.** After a fix, the next review compares the document with that copy and checks what
  changed, instead of reading everything again.
- **Code.** Git does the same: each review reads the changes since the last delivered part.
- **What it saves.** Less to read means less time and less of your Claude usage on every repeat
  review, and a change cannot hide in a long document.

### Why it works

The agent does not decide when the work is done; the score does. Every step is played the same
way every time, and every point has a record behind it. The way the work is done becomes predictable:
the same process, the same checks, the same proof, whatever is being built.

### The name

The name was found while searching for one. The author's own name, Metaxotos S., turned out to
describe what the plugin does, once it is split into parts:

- **Meta** means "beyond". The plugin works one level above the agent. It does not build your
  software; it governs how the agent builds it.
- **XoT** comes from an idea in AI research, "Everything of Thoughts" (XoT, Microsoft Research, 2023),
  where a separate guide steers a language model's thinking. This plugin is **not** that method, but it
  takes the same idea: something outside the agent should guide it. Here the guide is a score. The
  process becomes a vector, one number per step, and the numbers rise only as steps are completed and
  pass their reviews. Each number has a set maximum. The run ends only when all of them reach it, or when you choose to end it, and
  until then the agent may not stop, except to wait for your answer.
- **OSS** means open-source software, under the Apache 2.0 licence.
- **Rail** stands for the guardrails that keep the work on track. They stop the agent from changing its
  own score, skipping a step, approving its own work, or drifting from what you asked.

In Claude Code's messages the plugin calls itself MetaXoTRail.

## Why use it

### What you get

- **The agent cannot mark its own work as done.** A step closes only on two records the pipeline
  compares, and every step is checked by a reviewer that did not write it.
- **You answer business questions, not technical ones.** Claude asks about what the work should do —
  never which library, pattern or code. If the work needs a development stack your project does not have
  yet — language, framework, database, hosting, or a paid service — and you did not say which, Claude asks
  you once to choose: the best fit, the cheapest and the easiest to maintain, in business terms, with a
  recommendation. Most questions are multiple choice: options Claude prepared
  from its own study of the project, their pros and cons, and a recommendation. You click a choice, or
  write what Claude asked for.
- **Risky actions wait for you.** Some decisions are too important to leave to the agent: overriding
  the process (closing, reopening or sending back a step on your own authority), ending a run
  before it is finished, and commands that would delete folders or throw away work not yet committed.
  During a run, Claude cannot take any of them by itself. They happen only when you approve them — and
  your approval covers that one action only.
- **Problems are found where they start.** A review that finds a wrong plan sends the work back to
  the plan, and everything built on it loses its points until it is done again.
- **Finished work stays finished.** Once a part is built and reviewed, its code is frozen until it is
  delivered, and a git hook refuses to undo work the run has credited.
- **You keep the story of the work, not only the code.** Git shows what changed. The run's documents
  show why: how the code worked before, the options that were weighed, the plan and its assumptions,
  what each review found and how it was fixed. They are committed with each part. The run's history
  adds every step, your answers, and which steps rest on your word rather than a check.
- **The plugin sends nothing.** Its own code sends nothing over the network; Claude Code works as it
  always does, sending what you write and what Claude reads to Anthropic's model.

### Who it is for, and the problems it solves

- **You do not know the steps of a proper development process.** You tried building with Claude Code,
  and it did not finish the job — or it built something that worked once but was not robust, not tested,
  or not built the way software should be. Meta-XoT-OSS-Rail knows the steps and plays every one of
  them: the code is studied before it is changed, the change is planned before it is built, and every
  part is tested and reviewed before the next one starts.
- **You know how it should be done, but you are asked questions you cannot answer.** Claude stops to
  ask which library, which pattern, which design — technical questions that need a specialist. Here
  those decisions stay with the process and its reviews. You are asked about what the work should do,
  in plain words, usually with the options laid out and one recommended; the only technical choice you make is a
  stack the work needs and your project does not have.
- **You can set the guardrails yourself, but keeping them costs you your day.** You keep
  checking the agent, to be sure it did not skip a step or a test. And when you let it run on its own, it starts
  skipping steps and controls. Here the guardrails are hooks: they hold whether you are watching or
  not, and Claude cannot end its turn before the work is really done.
- **You have an idea, and you want a solid first version of it.** One request goes in; what comes out
  was mapped, planned, built and tested, part by part, with a record of every step.

### What it is built for

It is made for building features, one at a time. Seen a certain way, almost everything is a feature —
a fix, a plan, a design, a new screen — so you could even build a whole project with it, one feature
after another. For a whole product in one go, the author built a
full suite, a separate product with this plugin as its core (see [Is that all?](#is-that-all)).

### Is that all?

This plugin is the core engine: it builds one piece of working software at a time, through the whole
process. It does not plan a whole product. For that, the author built a full suite — from an idea, to
phases and tasks, each one built with this engine. It is a separate product. To ask about it, see
[Support](#support).

## Getting started

### What you need

- Claude Code 2.1.300 or later (the version it is tested on);
- `python3` on your `PATH` (tested with Python 3.14);
- a git repository with at least one commit: a run starts from the last commit, and refuses a folder
  without one.

Claude Code — tested in the terminal and in the VS Code extension. claude.ai and Cowork do not install the plugin:
claude.ai's chat does not run its hooks, so a run there could not be guarded, and Cowork is not tested.

It works with any language. Flutter, Python and Unity (C#) projects also get extra guidance.

### Install

In Claude Code:

```text
/plugin marketplace add morreus/Meta-XoT-OSS-Rail
/plugin install metaxotrail@metaxotrail
```

Or from a terminal:

```bash
claude plugin marketplace add morreus/Meta-XoT-OSS-Rail
claude plugin install metaxotrail@metaxotrail
```

Start a new Claude Code session afterwards, so the plugin's commands and instructions load fresh.

### Before your first run

1. **Commit or stash your own changes.** Each time a part of the plan is delivered, the run commits
   everything in the project that git does not ignore, so work of yours that is not committed would
   go into that commit.
2. **Switch Claude Code to auto mode.** Press Shift+Tab until the mode shows "auto", or start it with
   `claude --permission-mode auto`. In the default mode Claude stops to ask your permission for almost
   every command, so the run halts all the time; in `bypassPermissions` or `dontAsk` mode your clicks
   on its questions are not read.

### A first run

Open Claude Code in your project and type the command; do not paste it:

```text
/metaxotrail:00-ship add a CSV export to the orders page
```

Claude looks at the project, writes a few lines about what will be built and what it found, and shows
you a few choices:
start fresh, use work from earlier, or tell Claude more first. Your click starts the run. From then
on Claude plays the steps by itself, reports the score after each one, and stops only to ask you
something that is yours to decide.

### Your answers

You answer by clicking a choice, or, when Claude asks for information rather than a choice, by writing it. In
the rare case a click cannot be read, Claude writes the exact line for you to type. A reply such as "yes" or
"do it" is not read as an answer.

### Examples

**A feature, through every step:**

```text
/metaxotrail:00-ship let customers download their invoices as PDF
```

**A small change, through the short chain:**

```text
/metaxotrail:00-ship-lite change the "Save" button's label to "Save draft"
```

**One step on its own, outside a run.** Claude studies how part of the project works and writes it into
`docs/context_map_<name>.md`. No score is kept and nothing is enforced (see
[Using the skills on their own](#using-the-skills-on-their-own)):

```text
/metaxotrail:10-context-map how does sign-in work?
```

## How a run works

### The steps

The full chain has ten steps. The first four are played once; the last six once for each part of
the plan:

| Step | What happens | Then |
|---|---|---|
| Map | Claude studies the code and writes down how it works today | reviewed |
| Plan | Claude plans the change, in parts, each with how it will be tested | reviewed |
| Build | Claude builds one part | reviewed |
| Test plan | Claude writes how that part will be tested | reviewed |
| Test | Claude runs the tests and records what really happened | reviewed |

The short chain, `00-ship-lite`, has six steps: map, plan and build, each reviewed, with no test
steps. It is for small, low-risk changes.

How each review works:

- **A fresh reviewer.** Each review that can pass a step runs in a fresh agent that starts without the
  conversation, and
  works from the code and the run's records.
- **Pass or fix.** If it finds nothing that blocks, the next step opens. If it finds problems, Claude
  fixes them and the review runs again, until it passes.
- **Only an independent pass, or your own acceptance, counts.** Only a pass from an independent reviewer, or
  your own acceptance of the step (starting from your notes or plan, or closing it when the pipeline asks you),
  completes it: Claude may check its own fix between rounds, but its own check never earns the points.

### When something goes wrong

**In the work:**

- **A review finds problems.** Claude fixes them, proving each fix, and the same review runs again
  until it passes.
- **A review finds that an earlier step was wrong.** The run goes back to that step. Everything built
  on it loses its points and is done again.
- **The run reaches a point where no step can move forward.** The pipeline stops and asks you, with the
  choices you have.
- **The code changes after its review.** The step does not close. Either the change is a generated
  file, which belongs in `.gitignore`, or the code goes back to its build step — your decision.
- **A file that looks like a secret is not in git.** The delivery of the part waits until you add it
  to `.gitignore` or commit it yourself.
- **A command would undo or delete finished work.** During a run it is refused to Claude. During a run,
  from your own terminal, git refuses any command that would remove a commit (moving a branch back,
  deleting it); it does not stop commands that throw away changes not yet committed, such as
  `git checkout -- .` or `git clean`. Outside a run, some of them from Claude — such as `git reset --hard`,
  `git rebase`, `git clean -f` and `rm -r` — ask you to confirm first.

**With you:**

- **Claude needs a decision only you can make.** It asks once, on a short list of choices, and
  waits. Nothing moves until you answer. If you write your own answer under "Other" on the list:
  when Claude asked for information, it is your answer; when it asked you to choose, Claude tells you
  how it reads your words and asks you to click. Anything else you type in the chat is discussion:
  Claude answers it, and the question still waits.
- **You already have notes or a plan.** Claude can start from them, at the step they reach. The
  steps you skip are marked in the history as attested by you, not checked.
- **You close the window, or start a new one.** The run waits. In the new window, Claude asks you
  before moving the run there.
- **You want to stop.** Choose to end it. The run is closed with the score it reached, and its
  records are kept.

### When the run is finished

The run is finished when the score reaches its target: every step closed, for every part of the plan.
By then:

- **Each part of the plan is a commit** in your project, `<part> delivered`, holding everything the
  run built for it, with the run's documents. **Nothing is pushed**: review the commits and push them
  yourself.
- **The run's history is kept.** Ask Claude for the run's report to see every step, your answers,
  and which steps rest on your word rather than a check.
- **To file the run away,** type `/metaxotrail:94-clean-process`.

## Using the skills on their own

You don't have to start a run to use the plugin. Fourteen of its skills also work on their own, in your
daily work, whenever you want one step done well:

| Skill | What it does on its own |
|---|---|
| `/metaxotrail:10-context-map` | studies how part of the project works and writes it down, with what is still unclear |
| `/metaxotrail:11-review-map` | reviews that study, checking it against the code, the git history and the web |
| `/metaxotrail:20-plan-impl` | plans a change: the options, the assumptions, the rules the result must meet, the parts |
| `/metaxotrail:21-review-plan` | reviews the plan and looks for a simpler or safer way |
| `/metaxotrail:30-implement-plan` | builds one part of the plan and checks it by running it |
| `/metaxotrail:31-review-impl` | reviews what was built against the plan, file by file |
| `/metaxotrail:40-test-plan` | plans the tests: normal, unusual and error cases, each with a measurable result |
| `/metaxotrail:41-review-test-plan` | reviews the test plan for gaps and for tests that cannot fail |
| `/metaxotrail:50-test-impl` | runs the tests one at a time and records what really happened |
| `/metaxotrail:51-review-tests` | reviews the results, looking for passes that prove nothing |
| `/metaxotrail:92-fix` | applies a review's findings |
| `/metaxotrail:91-challenge` | takes a hard look at Claude's own last answer |
| `/metaxotrail:90-explain` | explains a change or a decision in plain, business words |
| `/metaxotrail:60-commit` | makes one commit, after checking the changes and scanning for secrets |

Each brings the same method as in a run — the same instructions, the same reviews, and the extra
guidance for Flutter, Python and Unity projects — but nothing is enforced: there is no score, and you
decide when to stop. Each step still needs the document of the step before it (a plan needs a map), and says
so if it is missing. A review you start yourself is Claude's own, unless you run
it in a fresh agent.

The other four commands belong to a run: `00-ship` and `00-ship-lite` start one, and `93-rollback` and
`94-clean-process` work only inside one. The run versions of the steps (`-gated`) are used only inside a
run and are not in your menu.

## Reference

### The commands

| Command | What it does |
|---|---|
| `/metaxotrail:00-ship` | the full chain |
| `/metaxotrail:00-ship-lite` | the short chain, for small changes |
| `/metaxotrail:10-context-map` … `/metaxotrail:51-review-tests` | each step on its own, outside a run (see [Using the skills on their own](#using-the-skills-on-their-own)) |
| `/metaxotrail:60-commit` | commit your changes after a secret scan, outside a run (a run commits each part itself) |
| `/metaxotrail:90-explain` | a plain-language summary of a change |
| `/metaxotrail:91-challenge` | a hard look at Claude's own last answer |
| `/metaxotrail:92-fix` | apply a review's findings |
| `/metaxotrail:93-rollback` | inside a run only: redo an earlier step a review found wrong |
| `/metaxotrail:94-clean-process` | end a run and file its records away |

Every command starts with `metaxotrail:` because Claude Code puts a plugin's name in front of its
commands, so two plugins never clash. The skills' own text names them without it, as `/00-ship`. Each step also has a `-gated` version that runs only inside a
run; it is not in your menu.

### What it changes on your machine

**Hooks.** It registers hooks on Claude Code's events:

- before every `Bash`, `Write`, `Edit` and `NotebookEdit` call, a guard that refuses writes to the run's
  records, to the plugin's hook scripts and to `.git/` in every project, and, while a run is live, writes to the code
  while it is frozen and commands that would undo or delete finished work;
- before every `Bash` call, a second guard that asks you to confirm commands such as
  `git reset --hard`, `git push --force` and `rm -r`;
- when you send a message, and when you click a choice, a hook that records your answer;
- when Claude tries to end its turn, a check that refuses while the target is not reached;
- when a session starts, a short note on where the run stands.

**Files and commits.**

- `.metaxotrail/` in the project: the run's records. It holds its own `.gitignore`, so git ignores it.
- `WORKING.md` and `TEST_RESULTS.md` in the project root: the run's working documents.
- `~/.claude/metaxotrail-anchor/`: one small file per run, which lets the run tell if its records
  were rebuilt.
- `.git/hooks/reference-transaction` in the project: a small git hook that runs the plugin's own
  file: while a run is live, git refuses any change that moves a branch or tag back or deletes it, from any
  terminal. It does nothing once the plugin is gone.
- The plugin's `bin/` folder, on Claude's command path while the plugin is on: it holds only a note, and no program.
- A git commit each time a part of the plan is delivered, `<part> delivered`, as
  `metaxotrail <metaxotrail@localhost>`. It takes **everything git does not ignore** (`git add -A`) —
  the part's code, the run's documents, and any changes of yours not yet committed. It is never pushed.

**The network.** The plugin's own code sends nothing over it. Claude Code works as it always does:
what you write and what Claude reads go to Anthropic's model. Its mapping and planning steps ask
Claude to search the web, as Claude Code can do in any session.

### Limits

- The write guard reads the command line. A command hidden inside another program or script can get
  past it.
- It guards the project it runs in. Another project's records, named by their full path, are not
  guarded.
- The git hook is not used in a git worktree, or where git is set to look for hooks elsewhere (such as
  husky); an existing hook of the same name is replaced.
- One run per project, in one window. You can open a second Claude Code window on the same project and
  work there as usual: it is not gated, but the run's records, its documents and its commits stay guarded
  there too.
  A second run in the same project is refused while the first is live.
- A run takes much longer, and uses much more of your Claude usage, than asking Claude directly: every
  step has its own review agent, and a review with findings runs again after the fix.
- It works in Claude Code only, by design: its `bin/` folder keeps claude.ai and Cowork from installing it — claude.ai's
  chat does not run its hooks, so a run there could not be guarded, and Cowork is not tested.
- It is tested on macOS. Linux and Windows are not tested.
- After an update, the conversation that was open keeps the old version's instructions. Quit Claude Code and
  start a new conversation (see Updating).

### Updating

Two ways to get a new version, and one to be told of it:

- **Automatically:** in Claude Code, run `/plugin`, open **Marketplaces**, choose `metaxotrail`, and select
  **Enable auto-update**. It is off by default for this marketplace.
- **By hand:**

  ```bash
  claude plugin update metaxotrail@metaxotrail
  ```

- **To be told when one is out:** on the plugin's GitHub repository, choose **Watch → Custom → Releases**.

What changed in each version is in [`CHANGELOG.md`](CHANGELOG.md).

When Claude Code tells you the plugin was updated — after `claude plugin update`, after you update it in `/plugin`,
or a notice ending "Run /reload-plugins to apply" or "… to activate" — quit Claude Code and start it again, in a new conversation,
before you continue a run. `/reload-plugins`, `/clear` and resuming the old conversation keep the old
instructions. In the new conversation, Claude asks you before moving the run there.

### Uninstalling

End any live run first: ask Claude to end it.

```bash
claude plugin uninstall metaxotrail
```

That is all. What the plugin wrote in your projects stays, and does no harm: the git hook it left does
nothing once the plugin is gone.

To clean up as well, remove what you no longer want:

| What | What it is | To remove |
|---|---|---|
| `.git/hooks/reference-transaction` | the git hook, in each project that ran the plugin | `rm .git/hooks/reference-transaction` in that project |
| `.metaxotrail/` | the runs' records and history | `rm -r .metaxotrail` |
| `WORKING.md`, `TEST_RESULTS.md` | the run's documents: the map, the plan, the test results | delete them, or keep them as your notes |
| `docs/context_map_*.md`, `docs/test_results_*.md` | documents the steps wrote when used on their own | yours to keep or delete |
| `~/.claude/metaxotrail-anchor/` | one small file per run, in your home folder | `rm -r ~/.claude/metaxotrail-anchor` |

To find the projects that have the git hook:

```bash
find ~ -type f -path '*/.git/hooks/reference-transaction' -exec grep -l 'reference_transaction.py' {} +
```

The `<part> delivered` commits hold the work the runs built. They stay in your project's history, like
any other commit.

## The project

### Contributing

This is the first public version. It has been tested a lot, but it can get better from the experience
of the people who use it, so your feedback is what it needs most. Open an
[issue](https://github.com/morreus/Meta-XoT-OSS-Rail/issues) for a problem, an idea, or an improvement you
would like to discuss: say what you typed, what happened, what you expected, and your Claude Code
version. A pull request is welcome as a suggestion too, but it cannot be merged here — please open an
issue for it instead.

To report a security problem, use **Report a vulnerability** on the repository's **Security and
quality** tab, not a public issue.

### Support

Meta-XoT-OSS-Rail is free to use, at home or at work, under the Apache 2.0 licence. If it helps you,
star the repository, or share a coffee with the author on [Ko-fi](https://ko-fi.com/stamatismetaxotos).
For questions, the full suite, or working together, contact the author on [LinkedIn](https://www.linkedin.com/in/smetaxotos).

### Licence

Apache License 2.0 — see [`LICENSE`](LICENSE). [`NOTICE`](NOTICE) credits the author, Stamatios
Metaxotos.

### Privacy policy

Meta-XoT-OSS-Rail collects no personal data and sends nothing anywhere. It has no server, no account, no
analytics and no tracking, and its own code makes no network connection. Everything it writes stays on your
computer, and is listed in [What it changes on your machine](#what-it-changes-on-your-machine): the run's
records and documents in your project, one small file per run in `~/.claude/metaxotrail-anchor/`, a git hook in
the project, and a local commit for each delivered part, never pushed.

The plugin runs inside Claude Code. What you write and what Claude reads go to Anthropic's model, as in any
Claude Code session, under Anthropic's own terms and privacy policy. The plugin adds nothing to that, and the
author receives nothing.

If you contact the author on GitHub, Ko-fi or LinkedIn, those services handle what you send under their own
policies.

### Terms of use

Meta-XoT-OSS-Rail is free software under the Apache License 2.0, and is provided "as is", without warranty of
any kind (sections 7 and 8 of the [`LICENSE`](LICENSE)). In plain words:

- **It guides an AI model; it does not control it.** The work is done by the model Claude Code runs. The model
  can be wrong: it can write code that does not work, give advice or explanations that do not hold, change or
  delete files, or make a commit you did not want.
- **The guards reduce risk; they do not remove it.** They ask before many risky actions and refuse some others,
  but they cannot catch everything.
- **You stay responsible** for reviewing the work, keeping backups and version control, and for anything you
  run, ship or publish with it.
- **No liability.** To the extent the law allows, the author is not liable for any loss or damage arising from
  its use, including lost or changed data, faulty code, or decisions made on its output.
- **Claude Code and Anthropic's models** are governed by Anthropic's terms. Meta-XoT-OSS-Rail is an
  independent project, not made or endorsed by Anthropic.
