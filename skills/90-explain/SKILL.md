---
name: 90-explain
description: Explains an issue, a change or a decision in short, plain business words. It says what the problem is, the proposed fix, why it was chosen and what it changes. For an overview, not a walk through the code.
disable-model-invocation: true
argument-hint: <the issue / change / decision to summarize>
---
**The rule for questions.** Before any question, first say you are going to ask. Give the context and the content, so the user understands. This is the last thing you write, after all tool calls. Then ask the question on a sheet. In a run, write that briefing as a message of its own, with no tool call, and end the turn there; the turn-end check sends you on to the sheet. End the briefing with a short block — your recommendation, and anything to act on — and put each option's cost in its description on the sheet as well: the sheet opens over the end of a long message. Each option's pros, cons and cost, and your recommendation, come in the briefing; anything to act on is in the chat as plain text, never only on the sheet (`${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md`, "Brief before you ask").


Explain in plain business terms: $ARGUMENTS

**Audience is non-technical** (a stakeholder, a manager, or yourself stepping back). Keep it short and jargon-free. Cover these, a few sentences each:

- **The issue** — what's wrong or what's needed, and why it matters (the real-world / user / business cost of leaving it as-is).
- **The proposed fix** — what will be done (or was done), in plain language. No code, no internal jargon.
- **Why this option** — briefly, why this approach was chosen over the alternatives (the cost / risk / time / outcome trade-off that made it the pick).
- **The impact** — what changes for the user or business: the benefit, what it costs or risks, who's affected, and any caveat to be aware of.
- **Assumptions & open items** (if any) — what was taken as given, and anything still unresolved or pending a decision. (This is what `/00-ship` asks for in its end-of-run summary.)

## Rules
- **Short and non-technical** — imagine explaining to a smart non-engineer. No code; define or avoid jargon.
- **Accurate** — base it on the real change/decision (read the context map / diagnosis / diff if they exist). Don't invent. If the "why" or the alternatives weren't recorded, say so or ask rather than guessing.
- **Lead with the issue and the impact** — that's what the audience cares about, not the mechanics.
- If nothing has been decided yet (no fix chosen), say what's still open instead of inventing one.
