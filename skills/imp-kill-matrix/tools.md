# Mutation testing tools: fast default, complete matrix on demand

Verify flags against the installed tool version. There is no universal mutation-testing CI gate. Start with coverage-directed, fail-fast, changed-code probes only when useful. Keep exhaustive runs outside blocking PR CI.

## JavaScript / TypeScript: StrykerJS

Install the core and the test runner for the project (Vitest, Jest, etc.). Example `stryker.config.json` for **diagnostic** runs:

```json
{
  "testRunner": "vitest",
  "coverageAnalysis": "perTest",
  "disableBail": false,
  "incremental": true,
  "reporters": ["json", "clear-text", "progress"]
}
```

- `coverageAnalysis: perTest` restricts each mutant to the tests that cover it; `disableBail: false` stops executing additional tests once one kills the mutant. Neither supplies a complete kill matrix.
- Scope `mutate` to changed, meaningful source paths; a PR-wide or whole-tree mutation run is not a default check.
- Persist Stryker's incremental report/cache between CI jobs **if** using incremental mode; otherwise every ephemeral runner starts cold. Cache invalidation and tool/version changes must be respected.
- Tune concurrency to available CPU and memory; too many test workers can make CI slower. Measure initial dry-run/setup time separately from mutation execution time.
- For a **manual full-matrix audit only**, enable `disableBail: true`, keep `coverageAnalysis: perTest`, and use the JSON report at `reports/mutation/mutation.json`. Tell `kill_matrix.py` `--full-matrix` only after verifying completeness.
- Investigate repeated test-runner restarts, static mutants, costly setup hooks, worker contention, and timeouts before raising CI timeouts.

## C# / .NET: Stryker.NET

Scope the run with the tool's supported changed-file/since mechanism. Keep bail enabled for diagnostic runs. Enable `disable-bail` only for a deliberate complete-matrix audit and verify the JSON reporting format before analyzing it.

## Java / Kotlin on the JVM: PIT

Run mutation testing on a limited `targetClasses` set, without `fullMutationMatrix`, for fast targeted diagnostics. For a scheduled/manual full audit, enable `fullMutationMatrix=true` with XML output and the appropriate test framework plugin (JUnit 5 needs `pitest-junit5-plugin`). A full mutation matrix is not suitable for routine PR gating.

## Tools without per-test kill data

| Stack | Tool | Targeted run |
|---|---|---|
| Python | mutmut | `mutmut run` on the relevant scope |
| Rust | cargo-mutants | `cargo mutants --in-diff <diff file>` |
| Go | gremlins | `gremlins unleash <package>` |
| Ruby | mutant | `bundle exec mutant run --use rspec '<Namespace>*'` (check licensing) |
| Swift | Muter | `muter` with a limited scope |

These can report survivors and other diagnostic results without proving which individual tests are redundant.

When a **complete** CSV kill matrix is explicitly requested, export a mutant patch, apply it, run all relevant tests with machine-readable results, collect *every* failing test, and revert the patch for each mutant. Write `mutant,status,killed_by` rows (test names separated by `|`), then run `kill_matrix.py <report> --full-matrix`. This is intentionally expensive, non-blocking audit work.

A partial matrix **cannot justify deleting tests**. Even a complete matrix is evidence for human/agent review, not an automatic deletion rule.
