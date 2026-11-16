# Security policy

## Report a problem privately

If you find a security problem in Meta-XoT-OSS-Rail, do not open a public issue. Use **Report a vulnerability** on
the repository's **Security and quality** tab, or go straight to the
[private report form](https://github.com/morreus/Meta-XoT-OSS-Rail/security/advisories/new). Only you and the
author can read it.

Security problems include a way around one of the plugin's guards (a command, file write or step it should have
refused), and anything that sends your data somewhere it should not go.

## What to write

- what you did, step by step, so the problem can be found again;
- what happened, and what you expected;
- the plugin version (in Claude Code, type `/plugin` and look at metaxotrail) and your Claude Code version
  (type `claude --version` in a terminal).

Leave out passwords, keys and private code.

## What happens next

The author answers in the same private report. A fix ships in a new version, and the [changelog](CHANGELOG.md)
says so. Only the latest version gets fixes, so update before you report.
