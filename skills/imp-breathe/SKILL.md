---
name: imp-breathe
description: Runs the IMP breathing cycle for a pull request. On the inhale, the agent explores and builds freely while recording Contract obligations; on the exhale, in the same PR, it folds the new code back into the existing system, deletes duplication and dead code, completes and executes the Contract, prunes tests, and leaves zero technical debt. Use when implementing a feature or change in an IMP repo, before opening or updating a PR, when cleaning up agent-generated code, or when the user mentions inhale, exhale, breathing, simplicity, or technical debt.
---

# Breathe in, breathe out

Every PR breathes. Agents add complexity by default, and the exhale is where simplicity happens. Both halves happen in the same PR.

## Before the inhale

- Name the story: which of this week's success criteria does this serve? If none, ask whether it should be done now.
- Read the Contract for the components involved, then only the code you need.
- If what to build is still unclear, run `imp-spike` first.
- Size the PR so both halves fit in one sitting. Boil the lake across a series of PRs, each complete and breathed. Unfinished work merges only behind an off flag.

## Inhale: sprawl, and write down what you learn

- Build the change end to end. Explore freely: try the obvious approach, add what seems needed, follow surprises. Don't polish yet.
- Once the shape is clear, boil the lake: empty, loading, and error states, edge cases, accessibility, telemetry, docs, migrations, admin paths. Completeness beats cleverness.
- The moment a behavior is agreed with the user, write it into the Contract as an obligation (`imp-contract`). Ask when the decision is a product call.
- Keep a short list of what surprised you. It drives the exhale.

## Exhale: fold it back

Work through this checklist before the PR leaves draft, and track it in your progress notes:

```
Exhale
- [ ] Fold in: find existing code that already does what the new code does (helpers, components, services, types). Reuse or merge it; never leave two ways to do one thing.
- [ ] Reshape: if the change shows an existing abstraction has the wrong shape, fix the shape now. A known-wrong shape does not live another day.
- [ ] Delete: dead code, unused parameters, flags and config nobody needs, spike leftovers, debug output, commented-out code, speculative abstractions.
- [ ] Zero debt: no TODO, FIXME, HACK, or temporary code added. Do it now, or decide it isn't needed.
- [ ] Name: identifiers use the system vocabulary in contract/README.md; new terms are added there.
- [ ] Convention: the code follows the repo's existing patterns; no new configuration where a convention would do.
- [ ] Contract complete: every behavior added or changed is an obligation; the obligation checklist was walked for each touched component.
- [ ] Contract executable: obligations have tests through the public boundary; check_contract passes with --strict.
- [ ] Tests earn their place: kill matrix on the changed code (imp-kill-matrix); redundant tests deleted; each survivor became an obligation or deleted code.
- [ ] Stranger's read: the diff reads as if the final design had been the plan all along.
```

Measure the exhale and report it: net lines in source and in tests, and abstractions added versus removed. A feature can grow the code, but an exhale that removed nothing deserves a second look.

If the exhale reveals debt outside this PR's scope, fix it in the very next PR, before new feature work.

## PR description

Fill these sections (the PR template from `imp-init` has them):

```markdown
## Contract
- Added: QUO-007 [idempotency] Duplicate quote requests return the original quote
- Changed: QUO-004 latency budget 150 → 120 ms (checkout timeout lowered)
- Retired: none

## Breath
- Inhale: what was explored, and what it taught us
- Exhale: what was folded back, reshaped, or deleted (net −120 lines in src/quote)
```

Then hand off to `imp-ship`.
