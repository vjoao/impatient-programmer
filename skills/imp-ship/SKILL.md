---
name: imp-ship
description: Ships an IMP pull request. Sizes its blast radius, runs automated checks and an adversarial model review, lets green merge itself where the team's policy allows, releases every merge behind a canary or flag with a known rollback, and watches it in production. Use when a PR is ready to merge in an IMP repo, when deciding how much human review a change needs, enabling auto-merge, deploying, rolling back, or when the user says ship it, merge it, or release it.
---

# Ship: green merges itself

The long-term goal is to need no human code review at all. The blast radius of a PR decides how close to that goal it gets today. Machines hold the bar; human eyes are saved for catastrophic risk.

## Preconditions

- The PR breathed (`imp-breathe`): the Contract is updated, the exhale is done, and the PR is labeled `fix` or `refinement`.
- The branch is current with its target.

## 1. Size the blast radius

Run from the repo root, adding any globs the repo's facts declare:

```bash
python3 <this-skill-dir>/scripts/blast_radius.py --base origin/<default-branch> \
  [--high '<glob>'] [--catastrophic '<glob>'] [--low '<glob>']
```

The script's level is a floor, based on paths, added lines (possible secrets, destructive data changes), diff size, and Contract changes. Then read the diff for meaning that paths can't show, such as money arithmetic in a utility file, a changed timeout, a removed retry, or a migration that rewrites rows. Raise the level when warranted. Only a human may lower it; record who and why in the PR.

| Level | Typical changes |
|---|---|
| low | Docs, tests, the Contract alone, paths the team marks low risk |
| medium | User-visible behavior, dependencies, anything a redeploy rolls back |
| high | Auth, permissions, money, personal data, public APIs and schemas, migrations, infrastructure and CI, removed or retired obligations |
| catastrophic | Irreversible data changes, security boundaries, the correctness of money movement, secrets, anything that can't be rolled back |

## 2. Run the automated checks

All required CI checks must be green, including the Contract check with `--strict`, relevant fast tests, lint, type checks, and security scans. Mutation testing (`imp-kill-matrix`) is an optional diagnostic, **not** a default blocking PR gate or a requirement for a complete kill matrix. If the repo currently marks a mutation job as required, change that policy through the normal approval process before merging; never bypass a required check. Never rerun a flaky check merely until it passes or quarantine tests to get a green merge; fix instability and preserve coverage of important behavior.

## 3. Adversarial model review

Launch a reviewer subagent that starts with an empty context, on a different model from the author when possible. A subagent that forks the current conversation, as Codex subagents can, is not fresh: ask for one that starts empty, or run the review as a separate session, such as `codex exec`. Give it only the diff, the Contract files touched, the relevant decision records, and the blast-radius output: never the author's reasoning or chat history. Brief it:

> Review this change to break it. Find every way it violates an obligation in the Contract, every obligation it should have added and didn't, every regression for existing callers, and every security, data, performance, and failure-mode risk. For each finding give file and line, a concrete scenario that fails, and a severity: blocker, should-fix, or nit. Default to suspicion. If you find nothing, list what you checked.

Resolve each blocker and should-fix: fix it, or rebut it with evidence (a test, a measurement, a Contract line). Review the new diff again. If blockers remain after two rounds, stop and hand the PR to a human.

## 4. Apply the merge policy

Use the repo's policy from its facts; otherwise use this default:

| Level | Gate before merge |
|---|---|
| low | Green checks and a clean adversarial review, then auto-merge |
| medium | As low, plus release behind a canary or flag; a human reads the Contract diff if obligations changed |
| high | A human reviews the Contract diff and the rollout plan, and reads code only where they choose |
| catastrophic | A human reviews code, Contract, and rollout; rehearse the rollback; never auto-merge |

Branch protection and org policy always win. When they require a human, prepare the PR so the review takes minutes: lead with the Contract diff, then the blast radius, evidence, and rollout plan.

Never bypass branch protection, use an admin merge, approve your own PR, or merge with a failing or skipped required check. On GitHub, `gh pr merge <number> --auto --squash` queues the merge until required checks pass.

## 5. Release every merge

Before merging, write in the PR:

- **Rollout:** how it reaches production: direct deploy, canary percentage, feature flag, or, for app-store clients, an internal or beta track plus a remote flag.
- **Watch:** the signals that prove it works, and the thresholds that trigger rollback: error rate, latency against the Contract's obligations, a business metric.
- **Rollback:** the exact command or switch (revert, redeploy the previous version, flag off) and who can run it.

After the merge, watch the signals for the agreed window. On a regression, roll back first, then fix forward through `imp-bugfix`. It reached production, so it is a fix.

## 6. Close the loop

Link the release or deploy in the PR, so the daily brief (`imp-heartbeat`) can pick it up.
