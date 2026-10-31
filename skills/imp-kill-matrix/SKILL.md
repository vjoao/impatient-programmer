---
name: imp-kill-matrix
description: Audits whether tests detect injected defects. Uses fast, scoped mutation probes when useful and a full kill matrix only on explicit request or in non-blocking scheduled audits. Helps interpret surviving mutants without making mutation score or test deletion a mandatory PR gate. Use when assessing test quality, pruning tests, setting up mutation testing (Stryker, PIT, mutmut, cargo-mutants), or investigating mutants, kill matrices, and mutation scores.
---

# Kill matrix: diagnostic evidence, not a release gate

Mutation testing deliberately changes code to see whether assertions detect the change. It can reveal weak tests, but it multiplies test runs; a *complete* kill matrix (every test that kills every mutant) is especially expensive. Optimize for a short feedback loop. Mutation testing is **not required** to finish an ordinary PR.

## 1. The mandatory quality bar

Before considering mutation testing, pass the repo's **required** type checks, lint, fast unit/integration tests, executable Contract checks, and security checks as applicable. Test observable behavior, boundaries, failures, and invariants. Every changed obligation should have a meaningful assertion. Use the test-to-obligation mapping from `imp-contract` to identify gaps.

Do not use line coverage, mutation score, or a kill matrix as a substitute for behavior-oriented tests.

## 2. Optional targeted probes (PR or local)

Only when the risk justifies the cost:

1. Mutate **changed business logic**, not generated output, trivial glue, or the whole tree.
2. Select tests that cover each mutant (`coverageAnalysis: perTest` in StrykerJS, when supported). Run mutants in parallel within the CI runner's capacity.
3. **Bail as soon as any test kills a mutant** (`disableBail: false` in StrykerJS). No full matrix is needed to establish detection.
4. Use a small deterministic mutant sample and a declared time budget (suggested additional 60 seconds); record how many mutants were actually executed. Sampling is not a full mutation score.
5. If the budget expires, report the probe **incomplete**, not passed. An optional probe must not turn into a mandatory, hanging gate.

Re-run or strengthen tests for meaningful surviving mutants. See [tools.md](tools.md) for stack-specific settings. Prefer an explicitly requested deeper audit when diagnostics need more time.

## 3. Full audit: opt-in or scheduled and non-blocking

For a component audit, regression investigation, or a separate scheduled/manual CI job:

- Run a broader but bounded mutation set. Persist incremental/cache results where the tool supports it.
- **Only when a complete kill matrix is explicitly needed**, record *all* killing tests (StrykerJS `disableBail: true`, PIT `fullMutationMatrix=true`). Expect higher cost.
- Analyze the report:

```bash
python3 <this-skill-dir>/scripts/kill_matrix.py <report> --contract-dir contract
# Use --full-matrix ONLY after verifying that all killing tests were recorded.
```

The analyzer accepts mutation-testing-report-schema JSON, PIT XML, or CSV. Reports that cannot prove complete kill attribution withhold test-pruning diagnostics. A full-matrix audit may identify candidates for review; **never automatically delete tests solely because they kill no unique mutant**. Tests also protect obligation boundaries, integration behavior, timing, safety, and failure modes that mutation operators may not express.

## 4. Interpret survivors

For each meaningful survivor: (a) strengthen an assertion or add a missing Contract obligation; (b) remove truly unused code in the exhale; or (c) document why a mutant is equivalent or irrelevant. Consider uncovered mutants separately. Do not chase a numeric score or delete useful tests just to improve it.

## 5. CI policy

- **Blocking PR checks:** fast tests, Contract, lint/typecheck/security as appropriate, and the existing repo-required checks.
- **Optional PR diagnostics:** targeted mutation probes with an explicit budget, never a full kill matrix.
- **Scheduled/manual audits:** full mutations and kill-matrix analysis as **non-blocking** reports; investigate findings in follow-up work.

When updating an existing repository, deliberately remove mutation thresholds or full-matrix jobs from **required** checks; adjust branch protection through the repo's normal approval process. Never bypass an existing required check to merge. Record this choice in a decision record and the repo's `AGENTS.md`.
