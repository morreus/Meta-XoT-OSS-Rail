---
name: 50-test-impl
description: Runs the test plan one test at a time and records what really happened, with evidence, as pass, fail or suspicious. It never invents a result. Use it after /40-test-plan.
disable-model-invocation: true
argument-hint: <feature being tested>
---

Execute the tests planned in the working document, `docs/context_map_<slug>.md`, one at a time.

**On the plan's highest-numbered milestone** — the integration one, which builds nothing by design —
the plan you execute is the release-level suite across everything the earlier milestones shipped.
The absence of milestone code there is not a finding; what breaks in the end-to-end run is.

**Which file.** `<slug>` names the work: the context map document is the one `/10-context-map` wrote for it, and the results file carries the same slug. If `docs/` holds more than one context map document and neither the request nor the conversation says which, ask.

## Prerequisites
- `docs/context_map_<slug>.md` holds the test plan. Read it fully NOW; note dependencies and order.
- Verify the environment **per the stack** (`${CLAUDE_PLUGIN_ROOT}/stack_rules/<stack>.md`): deps/venv installed, the test framework available, test data/fixtures in place.

**If the test plan is missing → STOP. Run `/40-test-plan` first.**

## SAFETY (production or money-moving code) — read before running anything
Never run a test that places a real order, writes production data, calls a live paid/irreversible API, or performs any action flagged in the context map's **Project-Risk Touchpoints**. Use dry-run / sandbox accounts / fixtures / mocks. If a test cannot be run safely, mark it **🚧 BLOCKED** and hand back — do NOT run it live.

---

## PHASE 1: Execute each test (in dependency order)
For EACH test:
1. **Pre-test** — state ID, name, category, priority, dependencies.
2. **Dependency check** — if a prerequisite test failed → SKIP with reason.
3. **Execute steps EXACTLY** — perform the action, observe the **ACTUAL** result, compare to EXPECTED.
4. **Collect real evidence** — actual output / log excerpt / metrics / screenshot (UI). Never copy the expected result in as the "actual".
5. **Verdict** — ✅ PASS (all steps + criteria met, evidence collected) / ❌ FAIL (any step or criterion missed) / ⏭️ SKIP (dependency/env) / ⚠️ SUSPICIOUS (passed but you're not confident) / ❓ INCONCLUSIVE (ambiguous, needs retest) / 🚧 BLOCKED (can't run safely).

---

## PHASE 1b: Prove the instrument can fail (MANDATORY before claiming a suite passes)

A test that cannot fail is worse than no test — it manufactures confidence. Before reporting an
automated suite green:

1. **Mutation check.** Deliberately break the thing under test (invert a condition, return a
   constant, comment out the effect). **Watch the relevant test FAIL.** Restore, watch it pass
   again. A test that stays green through the mutation proves nothing — report it as worthless,
   not as passing.
2. **Assert the expected count.** State how many tests you expect to run *before* running them, and
   compare. A stale build or an uncompiled change reports the OLD suite as green — the count not
   moving after you added tests is often the only visible symptom.
3. **Confirm the code under test actually executed.** Evidence like "the value stayed the same
   for the whole test" is equally consistent with the code never running. Prefer evidence that could only occur
   if the feature ran.
4. **Check your controls.** For any A/B, verify the "off" case is genuinely off — a component that
   switches itself back on makes the "off" case meaningless.

If a build or recompile is required, confirm it completed **before** interpreting results. Results
from a stale binary are not results.

## PHASE 2: Integrity self-check (per test — answer HONESTLY)
- Was this test actually performed (not assumed)?
- Robust enough to catch a real bug, or too easy?
- Relevant to the actual requirement?
- Could the feature be broken and this test still pass?
- Is the verdict honest — any hidden uncertainty?

**Red flags → mark SUSPICIOUS:** passed but you're not confident; trivially satisfied ("it didn't crash"); skipped steps assumed to work; evidence doesn't actually prove the pass; only the happy path was exercised.

---

## PHASE 3: Write the results file, `docs/test_results_<slug>.md`
A SEPARATE file — do **not** write results back into the test plan. They are deliberately separate:
every test ID declared in the plan is accounted for in the results, and collapsing them into one
document defeats that check entirely.

Required sections: Results · What failed · What was not run

Those three headings, exactly, are required, and inside a run they are checked for; write them as headings.
If a results file already exists, write INTO it below what is there, and never open it by
overwriting.

Per test: status, timestamp, an actual-vs-expected table, evidence, integrity flags, and any issues found (with severity per `_shared.md`).

## PHASE 4: Run summary
- Counts by status × priority (P0–P3).
- **Failed** tests (brief reason). **Suspicious** tests (need human review). **Skipped / blocked** (reason).
- Blocking issues. Release readiness: P0 and P1 status.

---

## RULES — integrity is non-negotiable
**DO:** actually perform each test; record ACTUAL observations; mark uncertain results SUSPICIOUS (not PASS); document every skip; collect real evidence; flag weak/too-easy tests.

**DO NOT:** mark PASS without performing it; copy expected results in as actual; hide uncertainty inside a PASS; fabricate evidence; assume behaviour without observing it; run any live/irreversible action.

**When in doubt → SUSPICIOUS or INCONCLUSIVE**, document what's uncertain, request human verification. Never default to PASS.

## Manual / device handoff
List any tests that require a human (device, UI judgment, physical action) with exact instructions, and wait for their results before finalizing the summary.

Stop after the summary. Do not proceed to fixes without approval.
