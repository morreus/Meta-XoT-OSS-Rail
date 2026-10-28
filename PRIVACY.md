# Privacy policy

*Effective 28 October 2026*

**Who we are.** Meta-XoT-OSS-Rail is a free, open-source plugin for Claude Code, made by Stamatios Metaxotos.
Contact: an issue on [GitHub](https://github.com/morreus/Meta-XoT-OSS-Rail/issues), or
[LinkedIn](https://www.linkedin.com/in/smetaxotos).

**What we collect about you: nothing.** The plugin has no server, no account, no analytics and no tracking. Its
own code makes no network connection. The author never receives your code, your answers or anything about you.

**What the plugin keeps on your computer.** While you use it, the plugin writes files on your own computer only:

- the run's records in `.metaxotrail/` and its documents (`WORKING.md`, `TEST_RESULTS.md`) in your project. They
  can contain your request, your answers and notes about your code;
- one small file per run in `~/.claude/metaxotrail-anchor/`;
- a git hook in your project, `.git/hooks/reference-transaction`;
- a local git commit for each delivered part, never pushed by the plugin.

These files are yours and stay under your control. You can delete them at any time; the README's "Uninstalling"
section says how.

**What goes to others.** The plugin runs inside Claude Code. Your messages, and what Claude reads in your project,
go to Anthropic to run the model, as in any Claude Code session, under Anthropic's privacy policy. Some steps ask
Claude to search the web, through Claude Code's own tools. If you push your project, open an issue, or contact the
author, GitHub, Ko-fi or LinkedIn handle that under their own policies.

**Your rights.** We hold no data about you, so there is nothing for us to give you, correct or delete. The files on
your computer you can read, change or delete yourself.

**Children.** The plugin is a tool for software work, not meant for children, and collects nothing from anyone.

**Changes.** A change to this policy is published in this file, with a new date, and noted in the
[CHANGELOG](CHANGELOG.md).
