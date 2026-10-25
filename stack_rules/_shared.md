# Shared rules (all stacks)

These apply to every MetaXoTRail skill regardless of stack. Stack-specific files extend them.

## Working principles
- **Evidence over claims.** Every assertion needs a receipt: file path + line, git commit, or web source. If you can't find evidence, mark it UNKNOWN — never guess.
- **Ask, don't assume — but only when it matters.** Ask the user ONLY when BOTH: (a) you can't resolve it from evidence (code/git/web/CLAUDE.md), AND (b) getting it wrong would change the approach or cause a real problem. For trivial, reversible, or obvious-default choices: pick the sensible default, state it, move on. Batch questions; never ask for the sake of asking. If you already know the likely answer and the cost of being wrong is low, don't ask — proceed and note the assumption. Zero questions is a fine outcome. **Never hand the user a technical choice** — a library, a pattern, how the code is built: decide it, give your reasons in the plan, and let its review check it. A technical unknown is settled from evidence or by a check in the plan's first part, never by asking. Still ask about what the work should do, for facts only the user has, and for actions only the user can take. The one exception is the development stack (`10-context-map`, §9), which sets cost and risk.
- **Brief before you ask.** Before any question — on a sheet or answered by typing — write in the chat, in plain business words, what the user needs to decide or act without having watched the work: what the work is and where it stands, what is to be decided and why now, the content it is about, the options with their pros, cons and implications, and your recommendation. As full as the decision needs; a few lines for a small one. When the question asks the user to do something, everything needed to do it — text to paste, a command, values, file names — is in the chat as plain text, never only on the sheet. The sheet holds the choices, one short line each. **Any price you state — money paid to a provider — is looked up, not remembered**: find it on a current source, name the source, and say it is an estimate the user must confirm with the provider — you are not responsible for it. If you cannot find it, say so; never give an old or guessed price.
- **Minimal diff.** Prefer modifying existing code over adding new files/abstractions. Match the project's existing conventions. No premature generalization (YAGNI).
- **Respect project safety rules.** Read CLAUDE.md for documented invariants, secrets, and irreversible/production operations. Never read or print secret files (e.g. `.env`). The MetaXoTRail safety hook asks the operator to confirm destructive git/`rm` operations — it does not hard-block them, so a confirmation prompt is not permission you have already been given; during a run, commands that would undo credited work are refused outright.

## Review severity (used by every review skill — 11, 21, 31, 41, 51 — and by the `/00-ship` loops)
Tag every finding HIGH, MEDIUM or LOW by one test — the same words every review skill quotes:

A finding is BLOCKING if, shipped as it stands, the system would do something wrong. A finding is LOW if it is true, worth recording, and changes nothing anyone does. A defect nothing can currently reach is LOW unless the change under review also supplies the path that reaches it. A finding about how a document reads — wording, a stale line number or cross-reference, a copy that disagrees without changing what gets built — is LOW; a document finding blocks only when someone building from it would do the wrong thing.

- **High** and **Medium** — blocking, by that test: the system would grant a permission it should refuse, credit work not done, lose or corrupt data or a record, fail open, break a documented project invariant about what the system does, or state something false that someone would build from. The two letters behave identically; both must be fixed before proceeding, and a reviewer unsure between them may pick either.
- **Low** — true, worth recording, changes nothing anyone does: style, naming, minor cleanup, and how a document reads. May be logged and carried forward.

A review **pass is "clean"** only when it surfaces **no High and no Medium** findings. Review loops repeat until a pass is clean (Low-only or none) — there is no fixed iteration cap; never proceed with open High/Medium items.

## Severity discipline (anti-nitpick — keeps review loops terminating)
- Do NOT inflate severity to justify another loop. Unsure between Medium and Low? Apply the test: would the system do something wrong — or, for a document, would someone building from it do the wrong thing? Nothing → Low.
- Style, naming, formatting, "could be cleaner", and nice-to-have refactors are ALWAYS Low — never Medium — unless they cause a real correctness/safety bug.
- A finding is High/Med ONLY if you can name the concrete failure: the input that breaks it, the invariant it violates, or the exploit. "I'd prefer X" is not a finding.
- Don't re-raise a finding that was downgraded or accepted in a prior pass.
- Convergence is expected: a healthy review reaches Low-only within a few passes. If you keep inventing new Med/High on the same code each pass, you're nitpicking — report clean and stop.

## Review loop (every gate: map / plan / implementation / tests)
Each stage is gated by a loop, not a single review:
1. Produce/refresh the artifact (map, plan, code, or test plan/results).
2. **Review** it with fresh eyes: an agent that did not write it (in a `/00-ship` run the review skill starts its own; otherwise review it yourself and say it was a self-review).
3. If the review has any **High/Med** findings → **apply the fixes/corrections** to the artifact with **`/92-fix`** (it edits per the producing skill's conventions; the review skills are read-only and never fix).
4. **Re-review** with fresh eyes. Repeat 3-4 until a pass is clean (no High/Med).
5. Only then advance to the next stage.
6. **Stuck = stop, don't ship.** If a High/Med can't be resolved (the fix doesn't work after a few honest attempts, or it's a genuine design problem you can't settle), do NOT loop forever and do NOT advance — STOP, warn the user with the specific blocker (what's failing, what you tried, options), and wait.

**Re-reviewing after a fix — what you look at, what you may take on trust, and what you may not.**
The first review of a loop sweeps everything. A later round is scoped, not relaxed: a fresh review
reads what changed since the last fresh review; a review of your own fix reads what changed since
the previous round; each then searches the whole artifact for the old wording of every line the
change touched, and checks whatever else the change could break. Within that scope the burden of
proof is unchanged. And you need not re-derive from scratch a claim that a
**named prior independent reviewer** already verified — spot-check it and name the round you are
relying on, so the chain stays attributable. This applies **only** to independent verification: a
claim the *author* made, however thoroughly documented, has never been checked by anyone and must be
verified in full the first time a reviewer reaches it. The distinction is the whole point: the common failure is
reviewers re-checking, round after round, what an independent reviewer already confirmed, while
figures the author produced go unchecked.

Applying-and-rechecking is automatic and does NOT require asking the user each loop; pause only for a genuine approach question (see "Ask, don't assume"), a hard safety/irreversible gate, or a stuck blocker (step 6).

**Tests are a hard gate.** A FAILED or SUSPICIOUS test counts as a High finding. Never mark a failing test as pass, never skip it to keep moving, and never reach `/60-commit` while any test is failing or unresolved — fix and re-run until green, or stop and warn the user. Green tests (or an explicit operator waiver) are required before commit.

## Bug-fix discipline (when the task is fixing a bug)
- **Reproduce first — owned by the context map.** Before any fix, the bug must be reproduced, ideally as a **failing test** (or minimal repro script) watched to FAIL. The map diagnoses: it reproduces the symptom and proves the root cause (that the cause actually produces the symptom). If it can't be reproduced, keep investigating and say so — don't guess-fix.
- **Root cause, not symptom.** Fix the confirmed cause with the minimal change; no symptom-patching, no opportunistic refactor.
- **Red → green → keep.** The reproduction test must FAIL before the fix and PASS after. Keep it as a permanent regression test so the bug can't silently return (red→green also proves the test isn't a false positive).
- **Regression sweep.** Run the existing test suite to confirm the fix didn't break anything else.

## Reporting honestly on things nobody can check
Inside a run, each review's close records who wrote it: the reviewer's own agent (`independent`) or the
orchestrator, the main Claude session driving the run. Only a clean `independent` close completes the step;
the orchestrator's own round never does. Outside a run, nothing checks the mark — say plainly when a
review was your own.
A review closes as independent only when the close comes from inside the reviewer's own agent —
nobody types that claim; the hook reads `agent_id` off the call, which Claude Code populates only
inside a subagent, and a close on an independent ticket from the main thread is refused. What that
proves is exactly this much: *the orchestrator did not write this verdict, and the record shows a
separate process did.*

What is still unchecked is everything that matters most: whether the delegated review was
thorough, whether it was honest, and whether the subagent was spawned to do the work or merely to
type the command. Those are worth exactly what your honesty is worth, and they are relied upon.

- **`independent` means a DIFFERENT agent or session — one that did not produce the artifact —
  performed the review.** Nothing else qualifies.
- Reviewing your own work carefully, adversarially, with fresh intent, after a break, or in a
  separate turn is **`self`**. Rigour is not independence. This is the distinction most likely to
  be blurred by motivated reasoning, so apply it literally.
- **Logging `self` is a correct, expected outcome**, not a failure: say it plainly, and never overstate.
  Inside a run it does not complete a step — the independent round still has to follow.
- Why it matters: outside a run nothing checks the mark, so a self-review written up as independent
  turns a green light into a false one. The `self`/`independent` mark on each review's close is the only thing standing between a
  green light and a false one.
- The same applies to every claim the gate can't check — test counts, "all P0 pass", whether a
  command was actually run. **Never report an outcome you did not observe.**

## Output discipline
- Read files fully before summarizing them.
- Be concise. Tables and short bullets over prose walls.
- When you stop, say exactly why and what you need to continue.
