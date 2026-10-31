---
name: imp-init
description: Sets up a new or existing repository for Impatient Programming. Detects the stack and existing conventions, asks only what it can't infer, and adds the IMP section to AGENTS.md, a system Contract, decision records, a guardrails log, PR template sections, fix and refinement labels, and fast CI checks for the Contract and blast radius, with mutation diagnostics optional and non-blocking. Use when the user wants to adopt IMP or Impatient Programming in a repo, start a new project the IMP way, or make a repo IMP-ready.
---

# Make a repo IMP-ready

Convention over configuration: add the defaults, record only what differs, and never overwrite what exists.

## 1. Discover

Read before asking:

- Agent files: `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/`.
- Stack, test command, CI provider and workflows, default branch, and how a merge reaches production (deploy workflows, release tags, app store pipelines, feature flags).
- Existing decision records (`docs/adr`, `doc/adr`, `docs/decisions`, `adr`), CODEOWNERS, PR template, and labels (`gh label list`).
- Whether mutation tooling exists, how expensive it is, and whether a mutation job is currently required. See `../imp-kill-matrix/tools.md`.

## 2. Ask once

In a single round of questions, ask only what the repo can't tell you, proposing an answer for each:

- The system's name and metaphor (offer a draft from the README and the code).
- The team space for stories, briefs, and showcases.
- The merge policy: the IMP default from `imp-ship`, or something stricter that org rules require.
- How a merge reaches production, if it isn't discoverable.
- Who the customer is.

## 3. Propose, then write

Show the plan (files to create, remote changes to make), then create only what is missing, using [templates.md](templates.md):

| What | Where |
|---|---|
| IMP section with the repo facts | `AGENTS.md`, or `CLAUDE.md` if that is the repo's agent file |
| System Contract | `contract/README.md`, from `../imp-contract/contract-template.md`, with vocabulary and a component index drafted from the code |
| First decision record | `docs/decisions/0001-adopt-impatient-programming.md`, or the next number in the existing folder |
| Guardrails log | `docs/guardrails.md` |
| PR template sections | `.github/pull_request_template.md`; append to an existing template |
| CI scripts | Copies in `scripts/imp/` of `../imp-contract/scripts/check_contract.py`, `../imp-kill-matrix/scripts/kill_matrix.py`, and `../imp-ship/scripts/blast_radius.py`, so CI doesn't depend on anyone's skill install |
| CI job | Required fast Contract check and blast radius report; mutation diagnostics opt-in/non-blocking |

Ask before each remote side effect:

- Labels: `gh label create fix --color d73a4a --description "Repairs a defect in code live in production"` and `gh label create refinement --color a2eeef --description "Any change that is not a production fix"`.
- A CODEOWNERS entry so the Contract's owners review changes to `contract/`.
- Allowing auto-merge in the repo settings (`gh repo edit --enable-auto-merge`). Never weaken branch protection.

## 4. Existing codebases: grow the Contract from the work

Don't backfill every Contract up front. Contracts grow as work touches components: every feature, bug, and drill adds obligations for what it touches.

- Offer to draft one component Contract now, for the riskiest component. Obligations inferred from code, tests, and docs go under `## Unconfirmed` until a human confirms each one.
- Do **not** run a whole-suite mutation baseline during setup. If useful, schedule a non-blocking, scoped audit later. Do not mass-delete tests from mutation results.
- If an existing PR workflow requires mutation scoring or a full kill matrix, propose a migration to optional diagnostics and scheduled/manual non-blocking audits. Update required-check settings only through the normal approval process; never skip a required check to merge.

## 5. Finish

Summarize what was created and what still needs a human. Suggest the first loop: post this week's story (`imp-heartbeat`), then take one change through `imp-breathe` and `imp-ship`.
