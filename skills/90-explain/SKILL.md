---
name: 90-explain
description: Explains an issue, a change or a decision in short, plain business words. It says what the problem is, the proposed fix, why it was chosen and what it changes. For an overview, not a walk through the code.
disable-model-invocation: true
argument-hint: <the issue / change / decision to summarize>
---

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
