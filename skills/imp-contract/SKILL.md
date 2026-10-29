---
name: imp-contract
description: Writes and maintains the IMP Contract, the in-repo, versioned set of numbered functional and non-functional obligations each component must meet, and makes obligations executable through tests tagged with their IDs. Use when recording an agreed behavior, starting or reviewing a Contract, adding non-functional obligations such as latency, timeouts, ordering, or idempotency, checking which obligations lack tests, or when the user mentions the Contract, obligations, invariants, or regenerability.
---

# The Contract

The Contract is the team's shared mental model of the system, written down in the repo in structured language that agents can use as a guardrail. It is not user stories: it states what the software must do, so that any component can be rebuilt from it. If a component cannot be rebuilt from its Contract, the Contract is missing something.

## Layout

- `contract/README.md` is the system Contract: the system's name and metaphor, its vocabulary, the component index, and cross-cutting obligations (prefix `SYS`).
- `contract/<component>.md` holds one component's Contract, with its own ID prefix.
- Contracts live outside component code, so a component can be deleted and rebuilt without losing them.

Start new files from [contract-template.md](contract-template.md). Follow the repo's facts if it declares another location.

## Obligations

Each obligation is a level-3 heading, `### <PREFIX>-<NNN> [<kind>] <title>`, under the `## Obligations` section, followed by one statement in EARS form:

| Pattern | Form |
|---|---|
| Always | The <component> shall <response>. |
| Event | When <trigger>, the <component> shall <response>. |
| State | While <state>, the <component> shall <response>. |
| Unwanted | If <condition>, then the <component> shall <response>. |
| Optional | Where <feature is enabled>, the <component> shall <response>. |

Add these lines when needed:

- `Why:` who relies on the obligation and what breaks without it. Required for non-functional obligations.
- `Verified by: manual — <how, and why it is not automated yet>`, only when no test can enforce it yet.

Rules:

- IDs are permanent. Never renumber or reuse one. Retire an obligation by changing its kind to `[retired]` and adding a one-line reason.
- State observable behavior at the component's boundary, never the mechanism. Write "rejects a second capture of the same payment", not "checks a mutex".
- Put numbers in non-functional obligations: "p99 under 120 ms at 50 requests per second", not "fast".
- One promise per obligation. Split compound statements.
- Use the system vocabulary from `contract/README.md`, and add new terms there.

Example:

```markdown
### QUO-004 [latency] Quotes return inside the checkout timeout
The quote service shall respond within 120 ms at p99 at 50 requests per second.
Why: checkout calls it with a 150 ms timeout; slower responses surface as intermittent checkout failures.
```

## When to write

- **During the inhale:** write an obligation the moment a behavior is agreed with the user, not at the end of the PR.
- **During the exhale:** walk [obligation-checklist.md](obligation-checklist.md) for each component the PR touched and add what is missing. By merge, the Contract captures every invariant the result must hold, functional and non-functional.
- **On a production bug:** the Contract was missing something. Follow `imp-bugfix`.
- **After a regeneration drill:** each gap becomes a sentence. Follow `imp-regen-drill`.

Never invent product behavior nobody agreed on. Put it under `## Open questions`, with a proposed answer and an owner, and ask.

## Make it executable

An obligation is executable when at least one test whose name contains its ID enforces it, such as `it("QUO-004 responds within 120 ms at p99")` or `test_quo_004_rejects_second_capture`.

- Test through the component's public boundary (API, events, UI), never its internals, so the test survives a rewrite.
- Put contract tests where the repo's facts say (default: a `contract` folder in the test tree), so a regeneration drill can keep them while deleting implementation tests.
- For timing, ordering, concurrency, and failure obligations, prove the test works: break the obligation on purpose (add a delay, reorder events, drop a retry) and watch the test fail.

## Check it

Run from the repo root:

```bash
python3 <this-skill-dir>/scripts/check_contract.py --contract-dir contract --tests test
```

It reports malformed or duplicate IDs, obligations without a `shall` statement, obligations no test cites (unless `manual`), and tests that cite unknown or retired IDs. Without `--tests` it scans the usual test folders. `--strict` also fails on untested obligations; use it in CI and before merge. `--json` gives machine output.

## Review

The Contract diff is the main review surface. When presenting a PR, lead with the obligations added, changed, and retired. A reviewer who reads only the Contract diff should understand what changed in behavior.

## Regenerability test

For each component touched, ask: could an agent holding only the Contract, the decision records, and the interfaces rebuild this so every caller keeps working? Every answer of the form "no, because the code also does X" is an obligation to write now.
