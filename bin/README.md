# bin

This folder holds no program. claude.ai and Cowork do not install a plugin that has a top-level `bin/` folder
(Anthropic, "Plugin structure and testing"), and MetaXoTRail uses that: its runs are guarded by hooks,
claude.ai's chat does not run hooks, and Cowork, which does, is not tested. So this folder keeps the plugin to
Claude Code, where it is tested and its runs are guarded.
