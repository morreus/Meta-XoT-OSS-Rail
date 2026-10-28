---
name: 40-test-plan
description: Plans the tests from the study, the plan and the code that was built. It covers normal, unusual and error cases, gives each test a measurable pass rule, and puts the riskiest first. Use it after /30-implement-plan, before /50-test-impl.
disable-model-invocation: true
argument-hint: <feature being tested>
---

## One milestone at a time — and a milestone may honestly have nothing to test

The test stages are counted per milestone: this plan covers **the milestone you were given**, not
the whole feature. The release-level suite — the cross-cutting matrix, the regression sweep, the
end-to-end — belongs to the plan's **highest-numbered milestone**, the integration one, which is
where defects that only appear *between* milestones are found. **On that milestone this plan IS
the release-level suite**: it builds nothing by design, and the absence of milestone code there is
not a finding and not a gap — plan the end-to-end run across everything the earlier milestones
shipped.

⚠️ **Some milestones have nothing to test, and saying so is a valid plan.** An assumption-validation
milestone's deliverable is the measurements themselves; a milestone that only prepares an
environment has no behaviour of its own. Write that, name why, and say what evidence stands in
place of tests. Do **not** invent scenarios to fill the section — hollow tests are worse than an
honest absence, because they pass. The reviewer at `41-review-test-plan` checks the claim, so it is
a statement on the record, not a way out.

ultrathink: Create a comprehensive, evidence-based test plan for: $ARGUMENTS

**Which file.** `<slug>` names the work: the context map document is the one `/10-context-map` wrote for it, and the results file carries the same slug. If `docs/` holds more than one context map document and neither the request nor the conversation says which, ask.

## Prerequisites
- `docs/context_map_<slug>.md` holds the map and the plan, with completed milestone(s); there is an implementation to test (or this is the highest-numbered milestone — see above).
- Read NOW: the context map (scope, **Project-Risk Touchpoints**, assumptions), the plan (Scale & Edge Cases, risks), the **actual diff** (`git diff` / `git diff --staged`, plus `git status --porcelain --untracked-files=all` and every new file, read in full), existing test patterns in the repo (grep for test files), and `${CLAUDE_PLUGIN_ROOT}/stack_rules/_shared.md` + `${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md` (the project's test commands + risk checklist).

**If the implementation is missing → STOP. Implement first (`/30-implement-plan`).**

---

## PHASE 1: Scenario discovery (every test must trace to a source)
- **From the context map** — entry points, data/state flows, Project-Risk Touchpoints.
- **From the plan** — assumptions to validate, the Scale & Edge Cases table, the risk list.
- **From the implementation** (read the diff) — public APIs changed, conditional branches, error paths, and the **stack-specific concerns from `stack_rules/<stack>.md`** (e.g. Python: dtype/precision, data leaking from the future, idempotency; Unity: lifecycle/serialization/UI; Flutter: async/rebuilds/platform).
- **From the web** (only for non-obvious areas) — common bugs/edge cases for this kind of change.

### Test-type checklist — walk EVERY type; each yields ≥ 1 scenario or is marked N/A with a reason
Forcing yourself through these is how you surface the edge cases the happy path hides:
- **Happy path** — typical valid input.
- **Boundary** — min/max, zero, one, empty, full, off-by-one, first/last element.
- **Invalid / negative** — wrong type, malformed, out-of-range, garbage input.
- **Null / empty / missing** — null, empty collection, absent field, defaults only.
- **Error & failure paths** — exceptions, timeouts, retries, partial failure, rollback/cleanup.
- **Idempotency / reproducibility** — run it twice; same input → same output (byte-identical for artifacts).
- **State & ordering** — repeated calls, out-of-order events, stale state, resume-after-interrupt.
- **Concurrency** — parallel access, races, locking, double-processing.
- **Scale / performance** — large inputs, memory, throughput, behaviour under load/timeouts.
- **Data integrity / precision** — dtype, rounding, very large/small numbers, encoding, truncation.
- **Time & timezone** — boundaries, DST, ordering, future/past dates.
- **External dependencies** — API errors, rate limits, network loss (mocked / dry-run — never live).
- **Security / secrets** — injection, authorization, and no secret/`.env` leakage in logs or output.
- **Regression** — pre-existing behaviour still holds.

Then add any **stack-specific types** from `stack_rules/<stack>.md` (e.g. Python: data leaking from the future in time-series; Unity: serialization/scene-reference breakage; Flutter: rebuild correctness).

---

## PHASE 2: Test plan output → `docs/context_map_<slug>.md`

**Write it INTO the working document**, below the plan — the map, the plan and the test plan are
one document. Never open the file by overwriting.

Required sections: What is tested · What is not tested · How to run it

Those three headings, exactly, are required, and inside a run they are checked for; write them as headings. The
scenarios, the coverage matrix and the prioritisation go under **What is tested**; the exclusions
and the honest *nothing to test* case under **What is not tested**; the commands, fixtures and
preconditions under **How to run it**.

**Categories — use the ones the stack actually has** (from `stack_rules/<stack>.md`), e.g.:
- **Automated** (unit/integration) in the project's framework (`pytest` / Unity Test Framework / `flutter test`).
- **Reproducibility / determinism** — same input → same output / byte-identical artifact (data & pipelines).
- **Manual / device / UI** — where human judgment or a device is needed (UI stacks: verify ≥ 2 aspect ratios).
- **Regression** — existing behaviour still works.

**Coverage matrix** — areas × test type.

**Per scenario** (T001, T002, …):
| Field | Content |
|-------|---------|
| ID / Name | T0NN / descriptive |
| Source | context map / plan / code / web |
| Priority | P0 (critical) … P3 (low) |
| Preconditions | required state/data — **and how you will arrange it** (see below) |
| Steps | action → expected observable result |
| Acceptance criteria | **measurable, pass/fail** — no "works correctly"; include perf/data thresholds where relevant |
| Edge cases | null/empty/boundary/failure/concurrency |
| Evidence | output / log excerpt / screenshot / metrics |

**Every precondition must be one you can ARRANGE.** For each scenario, say how its starting state
comes about: a fixture, an emulator or test instance, a seeded local database, a mock. "Production
happens to be in this state" is not an answer, and neither is waiting for it to become so.

This is not pedantry about wording. A plan whose preconditions depend on live state is not merely
unrunnable — it quietly pressures whoever runs it to *create* that state, and the states worth
testing are exactly the destructive ones: an empty queue, a deleted record, a failed payment.

If a scenario genuinely needs a state you cannot arrange safely, that is a finding about the TEST
ENVIRONMENT, and it belongs in the plan now: name what is needed (emulator, seeded instance,
fixture) as a prerequisite, or mark the scenario BLOCKED here with the reason — do not write it as
though it will run and leave the discovery to the person executing it.

**Risk-based prioritization** — map the highest-impact risks (and each Project-Risk Touchpoint) to the tests that cover them.

**Definition of Done** — all P0 pass; P1 pass on primary targets; no new errors/warnings; evidence collected.

**Excluded from testing** — list with justification (out of scope / covered elsewhere / risk accepted).

---

## PHASE 3: Test-quality self-check (challenge your own plan)
- Does every changed code path / branch have at least one test?
- Are acceptance criteria pass/fail and objective — not "looks right"?
- **Could the feature be broken and a test still pass?** (too-easy tests — fix them.)
- Is every Project-Risk Touchpoint covered by a test?
- Are edge cases and error paths covered, not just the happy path?
- Can every precondition actually be arranged? (see PHASE 2 — this is the one that gets skipped.)

**Then read the findings the earlier milestones' reviews raised, and check this draft against
what they already found.** Same-shaped artifacts collect same-shaped findings —
live-production preconditions, unfalsifiable acceptance bars, evidence lines that did not match the
step that produced them.

Do this AT THE END, as a check, not at the start as a template. Reading the prior milestone first
anchors you to its shape, and the point of a fresh plan is to notice what that one missed. Read
your draft, then read the findings, then look again at your draft.

Only the earlier milestones **of this work** — that is history the reviewers wrote down and you can
verify. Do not import "lessons" from elsewhere in the conversation.

---

## RULES
1. **Evidence-based** — every test traces to context map / plan / code / web.
2. **Measurable acceptance criteria only** — no vague "works".
3. **Categorize honestly** — don't mark a human-judgment test as automated.
4. **Prioritize by risk** — P0 covers the highest-impact scenarios.
5. **No live/irreversible actions in tests** — for production or money-moving code (e.g. anything in the context map's Project-Risk Touchpoints), tests use dry-run / sandbox accounts / fixtures, never real payments, orders or production writes.

Stop after creating the test plan. Do not execute tests.
