---
name: 91-challenge
description: Claude takes an honest, hard look at its own latest work before it is reviewed, whether a study, a plan, code, tests or an answer. It names real assumptions, missed details and things that will not scale, and never invents problems.
disable-model-invocation: true
argument-hint: <what to pressure-test (optional; defaults to your last output)>
---

ultrathink: Turn a brutally honest critical lens on your OWN output: $ARGUMENTS (default: the work you just produced).

You are red-teaming yourself before anyone else does. Be aggressive and unflinching — **but disciplined**: every criticism must be real and substantiated. Do NOT invent weaknesses, and do NOT tear down solid work to look rigorous — a manufactured flaw is a false alarm that wastes everyone's time. "This part is genuinely sound" is a valid, honest result.

## Interrogate your own work — with specifics (file:line / the exact claim), not vibes
1. **Assumptions** — what did I assume instead of verifying? Which are unverified AND load-bearing? Which could be wrong, and what breaks if they are?
2. **Missed details / gaps** — what did I NOT look at that could matter (callers, edge cases, config, tests, prior art, the project's invariants/risks)? What did I gloss over?
3. **Correctness doubts** — where am I least confident this is right? What's the weakest link?
4. **Scale / robustness** — what won't scale, breaks under load / large data / concurrency, or won't survive production? Where did I optimise only for the happy path?
5. **Overengineering / scope** — what's more complex than needed? What did I add that wasn't asked for? What simpler path did I skip?
6. **Evidence quality** — which claims rest on weak or no evidence? What wouldn't survive someone actually checking it?
7. **Blind spots** — what would a skeptical domain expert attack first?

## Discipline (keeps it honest, not theatrical)
- Tag each issue **High / Medium / Low** per `${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md` severity discipline; a real issue names the concrete failure (the input that breaks it, the invariant it violates). "Could be cleaner" is Low at most.
- **Do not manufacture problems.** If something is genuinely solid, say so plainly. Inventing flaws or downgrading good work to seem critical is itself a failure of this skill.
- Separate "this is wrong / risky" (a finding) from "I'd have done it differently" (preference — not a finding).

## Output
- **Honest verdict first** — solid / shaky / broken.
- **Findings** — worst-first: severity, location, the concrete problem, the fix.
- **What I'd fix before this goes to review.**
- If genuinely sound: say so, and name the 1–2 things you're least sure about (so it isn't blind confidence).

Then fix the High/Med yourself if you produced the work and can; otherwise hand back the honest critique.
