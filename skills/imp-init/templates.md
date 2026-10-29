# imp-init templates

Replace every `<placeholder>`. Leave out rows of the facts table whose default applies.

## AGENTS.md section

````markdown
## Impatient Programming

This repo follows Impatient Programming (IMP). Agents: load the `impatient-programming` skill before planning or changing code here. Read the Contract before the code, and record obligations as they are agreed. A change that alters behavior updates `contract/` in the same PR. Label PRs `fix` only for defects live in production, and everything else `refinement`. Add no TODOs or temporary code, and never bypass branch protection.

| Fact | Value |
|---|---|
| Contract | `contract/` |
| Contract tests | `<test folder>/contract/`; test names carry obligation IDs |
| Test command | `<command>` |
| Mutation command | `<command>`, report at `<path>` |
| Decision records | `docs/decisions/` |
| Guardrails log | `docs/guardrails.md` |
| Merge policy | IMP default (see `imp-ship`), or `<stricter policy, and why>` |
| Low-risk paths | `<globs>` |
| High-risk paths | `<globs>` |
| Catastrophic paths | `<globs>` |
| Release | `<how a merge reaches production; canary or flag mechanism; rollback command>` |
| Team space | `<channel or page>` |
| Customer | `<who>` |
````

## PR template sections

````markdown
## Story
<!-- Which of this week's success criteria this serves. -->

## Change type
- [ ] `fix`: repairs a defect in code live in production (link the evidence)
- [ ] `refinement`: everything else

## Contract
<!-- Reviewers start here. Obligations added, changed, and retired: ID, kind, one line each. -->

## Breath
- Inhale:
- Exhale:

## Evidence
<!-- Checks, contract check, kill matrix (score, tests deleted), screenshots or production links. -->

## Blast radius
<!-- low, medium, high, or catastrophic, with reasons. Rollout, watch signals, rollback. -->
````

## First decision record

````markdown
# 0001. Adopt Impatient Programming

Date: <YYYY-MM-DD> · Status: accepted · Decided by: <names>

## Context
<Why the team is adopting IMP now.>

## Decision
We work the Impatient Programming way: Contract-first pull requests that breathe, tests that earn their place through mutation testing, guardrails so no agent repeats a mistake, green merges itself within our blast-radius policy, every merge is released, and a weekly story and showcase. Our repo facts live in AGENTS.md.

## Consequences
- The Contract in `contract/` is the main review surface.
- PRs are labeled `fix` or `refinement`.
- <Where our policy differs from the IMP defaults, and why.>
````

## Guardrails log

````markdown
# Guardrails

Every mistake a person or an agent made once, and the software that now stops it from happening again. Newest first. Each entry gives the date and class of mistake, what happened, the guardrail and where it lives, and the proof that it rejects the mistake and accepts correct code.
````

## CI job (GitHub Actions)

````yaml
name: imp
on: pull_request

jobs:
  imp:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Contract
        run: python3 scripts/imp/check_contract.py --contract-dir contract --strict
      - name: Blast radius
        run: |
          {
            echo '```'
            python3 scripts/imp/blast_radius.py --base "origin/${{ github.base_ref }}"
            echo '```'
          } >> "$GITHUB_STEP_SUMMARY"
      - name: Mutation gate
        run: |
          <mutation command, scoped to the changed files>
          python3 scripts/imp/kill_matrix.py <report> --min-score <team threshold>
````
