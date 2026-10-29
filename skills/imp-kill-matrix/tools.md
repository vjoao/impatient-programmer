# Mutation testing tools

These are the settings that matter for a complete kill matrix. Check flags against the tool's current documentation before relying on them.

## JavaScript and TypeScript: StrykerJS

```bash
npm i -D @stryker-mutator/core @stryker-mutator/<runner>   # jest-runner, vitest-runner, mocha-runner, karma-runner
```

`stryker.config.json`:

```json
{
  "testRunner": "<runner>",
  "coverageAnalysis": "perTest",
  "disableBail": true,
  "reporters": ["json", "clear-text", "progress"]
}
```

- `perTest` records which tests cover each mutant; `disableBail` records every killing test, not just the first.
- Scope a PR with `npx stryker run --mutate "<changed files>"`. `--incremental` reuses results for unchanged code.
- Report: `reports/mutation/mutation.json`.

## C# and .NET: Stryker.NET

```bash
dotnet tool install -g dotnet-stryker
dotnet stryker --reporter json --since:<target-branch>
```

- Turn on `disable-bail` in `stryker-config.json` to record every killing test.
- Report: `StrykerOutput/<timestamp>/reports/mutation-report.json`.

## Java and Kotlin on the JVM: PIT

Maven:

```bash
mvn org.pitest:pitest-maven:mutationCoverage \
  -DoutputFormats=XML,HTML -DfullMutationMatrix=true -DtargetClasses='com.example.quote.*'
```

- `fullMutationMatrix` requires XML output, and records `killingTests` and `succeedingTests` for every mutant.
- JUnit 5 needs the `pitest-junit5-plugin` dependency.
- Gradle: the `info.solidsoft.pitest` plugin with `outputFormats = ['XML']` and `fullMutationMatrix = true`. Android JVM unit tests: the `pl.droidsonroids.pitest` plugin.
- Report: `target/pit-reports/mutations.xml` (Maven) or `build/reports/pitest/mutations.xml` (Gradle).

## Tools without per-test kill data

| Stack | Tool | Run |
|---|---|---|
| Python | mutmut | `mutmut run`, then `mutmut results`; `mutmut show <mutant>` prints the mutant's diff |
| Rust | cargo-mutants | `cargo mutants --in-diff <diff file>`; mutant diffs land in `mutants.out/` |
| Go | gremlins | `gremlins unleash <package>` |
| Ruby | mutant | `bundle exec mutant run --use rspec '<Namespace>*'`; check its license for commercial use |
| Swift | Muter | `muter init`, then `muter` |

These report which mutants survived, which is enough for the mutation score, the survivors, and a CI gate. To find redundant tests, build the full matrix yourself, scoped to the PR's mutants:

1. Export each mutant as a patch.
2. For each patch: apply it, run the whole suite with a JUnit XML reporter, record the failing tests, and revert.
3. Write one CSV row per mutant: `mutant,status,killed_by` (`killed` or `survived`, failing tests joined by `|`). Add a `covered_by` column if coverage is known.
4. Run `kill_matrix.py` on the CSV with `--full-matrix`.

This costs one suite run per mutant, the same as a mutation run without bail.
