---
name: imp-kill-matrix
description: Makes every automated test earn its place. Runs mutation testing, builds a kill matrix of which tests kill which mutants, deletes tests that catch nothing no other test catches, and turns surviving mutants into Contract obligations or deleted code. Use when pruning or auditing a test suite, when agents generated many tests, when setting up mutation testing or a mutation gate in CI (Stryker, PIT, mutmut, cargo-mutants, and others), or when the user mentions mutation testing, mutants, kill matrix, mutation score, or redundant tests.
---

# Kill matrix: every test earns its place

Agents will happily write thousands of tests, and every one burns CPU on every run. A test stays only if it catches something no other test catches. Mutation testing measures that: each mutant is a small deliberate bug, and a test kills it by failing.

## 1. Set up the tool

Pick the tool for the stack and configure it to record every killing test, not only the first. See [tools.md](tools.md). From a partial matrix, a redundant test and a test that merely ran second look the same, so never delete tests based on one.

## 2. Scope the run

- In a PR, mutate only the changed source files.
- For an audit or a regeneration drill, mutate one component at a time.
- Whole-codebase runs belong in a scheduled job, not the PR loop.

## 3. Build the matrix

```bash
python3 <this-skill-dir>/scripts/kill_matrix.py <report> --contract-dir contract
```

It reads mutation-testing-report-schema JSON (StrykerJS, Stryker.NET), PIT `mutations.xml`, or a CSV with `mutant,status,killed_by` columns (test names separated by `|`). It reports:

- the mutation score, and the survivors with location and mutator;
- **redundant** tests: every mutant they kill is also killed by a test that stays;
- **zero-kill** tests: they ran against mutated code and killed nothing;
- **protected** tests: the only test citing an obligation ID, with no unique kill;
- the retained set, in which each test kills at least one mutant no other retained test kills.

It withholds deletion advice when the report looks like the tool stopped at the first killing test. `--json` gives machine output, and `--min-score N` exits non-zero below N percent, for CI.

## 4. Act on it

- **Redundant and zero-kill tests:** delete them in the same PR, and give the count in the PR's Evidence section.
- **Protected tests:** keep them, because the obligation needs an executable form. Strengthen each one until it kills mutants in the code that implements its obligation. Mutation tools can't express timing, ordering, or failure obligations, so for those, prove the test by breaking the obligation on purpose (add a delay, drop a retry) and watching it fail.
- **Survivors:** each one is one of three things.
  1. A missing obligation: a caller would notice the change. Write the obligation (`imp-contract`) and a test that kills the mutant.
  2. Unneeded code: nothing anyone relies on changes. Delete the code as part of the exhale.
  3. An equivalent mutant: the change can't alter behavior. Ignore it, or exclude it with the tool's ignore mechanism and a reason.
- Re-run until the changed code has no unexplained survivors.

## 5. Keep it enforced

Add a mutation gate for changed files to CI (`--min-score`, or the tool's own threshold), so the rule runs in a machine instead of depending on anyone remembering it.
