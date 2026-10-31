---
name: imp-regen-drill
description: Runs an IMP regeneration fire drill. Copies the repo without history, deletes one component, has fresh agents rebuild it from only its Contract, decision records, interfaces, and contract tests, then compares the rebuilds to find gaps in the Contract, weak tests, and latent bugs. Use when checking whether a component is regenerable, testing how complete a Contract is, considering a rewrite or a port to another language, or when the user mentions regeneration, regenerative software, or fire drills.
---

# Regeneration drill

Keep everything regenerable, the way you run a fire drill without burning the building down. Regenerate for real only when it's worth doing, but drill often: if a component can't be rebuilt from its Contract, the Contract is missing something.

## 1. Pick and prepare

- Choose a component that has a Contract (`contract/<component>.md`) and contract tests. If it has neither, that is the finding: start with `imp-contract`.
- The rebuild may use the component and system Contracts, the decision records, the interfaces (types, schemas, API specs), the contract tests, and the rest of the codebase, including callers.
- The component's implementation, its implementation-level tests, and git history are off limits.

## 2. Make isolated copies without history

```bash
DRILL="$(mktemp -d)/<component>-drill-a"
mkdir -p "$DRILL" && git archive HEAD | tar -x -C "$DRILL"
rm -rf "$DRILL/<component code paths>" "$DRILL/<component implementation tests>"
cd "$DRILL" && git init -q && git add -A && git commit -qm "drill baseline"
```

Install dependencies in the copy. Make two or three copies, so independent rebuilds can be compared.

## 3. Regenerate

Each rebuild needs an agent that starts with an empty context, because this conversation may contain the code being rebuilt. If your agent's subagents fork the conversation, as Codex subagents can, run a separate session in each copy instead, such as `codex exec` started in the copy's folder. Give each copy to a fresh subagent with only its path and this brief, using different models across copies when possible:

> Rebuild the <component> component in this repository from contract/<component>.md, contract/README.md, docs/decisions/, and the interfaces it must satisfy. Do not access any other copy of this repository or any git remote. Make every contract test pass. Wherever the Contract is silent and you must choose, record the choice and the alternatives you considered in DRILL-NOTES.md.

## 4. Evaluate

In each copy:

- Run the contract tests and the full suite, including callers' tests.
- Optionally run a bounded, scoped mutation probe against the regenerated code using only the Contract tests (`imp-kill-matrix`). Compare its score with the old suite's score only as diagnostic evidence; a timed-out, fail-first, or partial report is incomplete, and a complete matrix belongs in a separate manual or scheduled non-blocking audit.
- Run the same inputs (scripted scenarios, recorded requests, or property tests) through every copy and the original. Every divergence marks a place where the Contract is silent.

## 5. Harvest

- Each divergence or recorded choice becomes a sentence in the Contract: an obligation if callers care, a Latitude entry if they don't.
- Each failing caller test is a missing obligation.
- A defect found in the original goes through `imp-bugfix`.
- Write a drill report in the decisions folder (inputs, copies and models used, results, gaps added, verdict) and update "Last regeneration drill" in the Contract's header.
- Delete the copies. Replace the original with a rebuild only as a deliberate decision, through a normal PR.

The drill passes when the contract tests pass in every copy, callers' tests pass, and the copies agree on everything callers can observe.
