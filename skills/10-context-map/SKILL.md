---
name: 10-context-map
description: Map relevant code paths and gather evidence before proposing solutions. Read-only, stack-aware exploration. Invoke explicitly before planning a change or investigating a feature.
disable-model-invocation: true
argument-hint: <feature or area to map>
---

ultrathink: Build a receipts-first context map for: $ARGUMENTS

## Where it goes

The map is written **into the working document**, `docs/context_map_<slug>.md` — the one
document the map, the plan and the test plan share, so every later step compares itself against
the one before it in one file. If the document exists, write into it below whatever is there, and
never open the file by overwriting; if you were told the work is a bug diagnosis rather than
a new design, say so in `## 0. The request` and map the path to the symptom.

**The file's name.** `<slug>` is a short lowercase name for the work, taken from what you were asked to map — `csv-export` — and every later step on the same work reads and writes the same file. If `docs/` holds more than one context map document and the request does not say which, ask.

Required sections: What this is · How it works today · What is unclear

Those three headings, exactly, are required, and inside a run they are checked for. The numbered sections below are the
method that fills them: §0 opens the document, above the three headings; §1–§3 go under **What this is**,
§4–§6 under **How it works today**, §7–§9 under **What is unclear**; §10 is your own check, and what it
finds goes into §7 or §9. Write the headings as headings; a sentence that mentions them has not
written them.

## PHASE 0: Stack & Project Calibration (do this FIRST)

Never assume a framework — establish what this project is, then load its rules:

1. **Detect the stack** from project markers: `*.csproj` + `Assets/` + `ProjectSettings/` -> unity-csharp; `pubspec.yaml` + `lib/*.dart` -> flutter; `requirements.txt`/`pyproject.toml`/`*.py` -> python; `package.json` -> node; etc.
2. **Read the shared + stack rules**: `${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md` and `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md`. They define conventions, test/lint/build commands, instrumentation style, the risk checklist, and the review-severity scheme. If the matching stack file is missing, say so and fall back to sensible defaults for the detected stack.
3. **Read CLAUDE.md** (root + nested) for *project-specific* invariants and safety protocols (data/file invariants, secrets, irreversible or production/money-touching operations).
4. Record: detected stack + the stack-rule highlights that apply + the project risks this change could plausibly touch. These calibrate every later section.

## PHASE 1: Evidence Gathering (MANDATORY)

### Codebase Exploration
Search the repo thoroughly before drawing conclusions:
- Glob for relevant file patterns
- Grep for related symbols, constants, error messages
- Read all files that could be involved
- Check imports and dependencies of discovered files

### Git Archaeology
- `git log --oneline -20 --all -- <relevant paths>` — recent changes to this area
- `git log -S "keyword" --oneline` — when was this pattern introduced/changed?
- `git blame <file>` — who owns this code, why was it written this way?

### Web Research
Search for: "[detected stack/language/framework] + [pattern/problem] + [best practices OR known issues]"
- Established patterns for this problem type
- Stack-specific gotchas (lifecycle, serialization, concurrency, platform)
- Known antipatterns to avoid

---

## PHASE 2: The map

**The map describes rather than designs; the plan chooses the design.** It records the code as it
is, what is unknown, and what the operator decides. It does not write how the new code will work —
its flow, its stages and their order, its checks, its schemas, or its assumptions about how the new
code will behave: that is the plan's, and a design
written here is reviewed twice, once as the map and again as the plan. A design decision that is the operator's —
which of two designs of what the user sees or does — is still asked here, as a question; the map records their answer, and
the plan builds the design from it.

### 0. The request
**Record $ARGUMENTS verbatim, first, before anything else**, under the heading `## 0. The request`.
The operator's own words, unedited — not your paraphrase, not your interpretation, not tidied up.
If they were vague, the vagueness is part of the record; raise it in §9 rather than resolving it
silently here.

This exists because every later check compares one document against the one before it: the plan
against the map, the code against the plan. Nothing compares the finished work against what was
actually asked for. A plan that quietly drifts, faithfully implemented, passes every review and
delivers the wrong thing correctly. `/21-review-plan` and `/31-review-impl` both check against this
section, so it has to be what you were told, not what you concluded.

## What this is
### 1. Entry Points
Who/what triggers this flow?
| Trigger | File | Symbol | Evidence |
|---------|------|--------|----------|
| ... | `path/file` | `MethodName()` | Line X |

### 2. Data & State Flow
```
[Source] -> [Transform] -> [Destination]
```
The flow of the code as it is today; new code appears only as the entry point the request names.
- What data moves where? What state is read/mutated? Persistence involved?

### 3. Stack-Specific Specifics (only the rows that apply)
Adapt to the detected stack:
- **UI stacks (Unity / Flutter / web):** render/layout model, resolution/aspect/device dependencies, nested layout containers.
- **Data / services / pipelines:** input & output schemas of the code as it is today, dtype/precision invariants, external API calls, idempotency/reproducibility, persistence & file writes.
- **Any stack:** concurrency/parallelism, serialization/format compatibility, secrets/credentials touched.

## How it works today
### 4. Files & Symbols Involved
| File | Key Symbols | Role | Last Modified |
|------|-------------|------|---------------|
| `path/file` | `Class.Method()` | ... | `git log` date |

### 5. Prior Art Found
| Pattern | Location | Applicable? |
|---------|----------|-------------|
| ... | `path/file:L42` | Yes/No — reason |

### 6. Web Findings
| Topic | Source | Key Insight | Applies? |
|-------|--------|-------------|----------|
| ... | URL/docs | ... | Yes/No |

## What is unclear
### 7. Unknowns & Assumptions

**Cannot determine from repo evidence:**
| Unknown | Why it matters | How to validate |
|---------|----------------|-----------------|
| ... | ... | Ask user / Test / Research |

**Assumptions made** — about the code as it is and the request, not assumptions about how the new
code will behave (which inputs it accepts, what it raises): those are the plan's to decide, and a
behaviour the operator must choose is a question (§9).
| Assumption | Confidence | Based on |
|------------|------------|----------|
| ... | High/Med/Low | [File/Git/Web] evidence |

### 8. Project-Risk Touchpoints
Does this change touch anything CLAUDE.md (or the stack risk checklist) flags as an invariant, secret, or irreversible/production operation?
| Touchpoint | Rule that applies | How to respect it |
|------------|-------------------|-------------------|
| ... | ... | ... |
(If none: state "None identified.")

### 9. Clarifying Questions
**Interview the user.** This is the phase where the concept is shaped, and the questions are the
most valuable thing in it — they reduce assumptions, get you aligned, and surface points the user
may not have considered. Challenge the request's own assumptions; turn anything fuzzy into
something concrete.

**Anything you would otherwise have to assume becomes a question here.** Do not quietly pick a
default on a point that changes the work. Max 7, and only what you genuinely cannot answer from
the evidence you gathered — don't manufacture questions to look thorough, and don't ask what the
codebase already told you.

Never a technical choice (`_shared.md`, "Ask, don't assume"). **The development stack is an exception**: when the
work needs a stack the project does not have yet — language, framework, database, hosting, a paid service — and
neither the project, the request, the user's answers nor a document they gave names it, ask it **last**, on its
own, once the other answers are in. Offer three: **the best fit** for the requirements, in your view — your
recommendation, first; **the cheapest**, free if a free one exists; **the easiest to maintain**. When two of these
are the same stack, merge them and say so; never invent a weaker option to fill a place. For each: its cost, pros,
cons, what it means later, how fast it reaches a first version compared with the others, how easy it is to move
away from, and whether MetaXoTRail has extra guidance for it. If all three are the same stack, offer it with the
closest alternative and say why the others merged. **Prices come from the web, never from memory**: what you
remember may be out of date. Look each one up on the provider's own page, name the source, and state that it is an
estimate the user must confirm with the provider, and that you are not responsible for it. If you cannot find a
current price, say so — never give an old or guessed one.

1. ...

### 10. Self-critique (do this BEFORE you finalize)
Red-team your own map:
- Weakest receipt? Which claim would not survive someone actually opening the file?
- What did you NOT read that could change the picture (callers, config, tests, sibling modules)?
- Are findings backed by **concrete codebase patterns (file:line)**, not generic description?
- What are you quietly assuming? Move each such assumption into §7 or §9.

Fix the gaps you can; list the rest as unknowns/questions.

---

## Rules
- Do NOT propose fixes or solutions yet
- Do NOT write implementation code
- Detect and respect the project's stack and CLAUDE.md conventions — never assume a framework
- If you cannot find evidence for something, mark it as UNKNOWN — do not guess
- Every claim must have a receipt: file path, git commit, or web source
- Read files fully before summarizing them
- Surface any project-specific invariant/safety rule this change could touch
