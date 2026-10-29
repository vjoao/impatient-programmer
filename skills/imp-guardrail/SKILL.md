---
name: imp-guardrail
description: Turns a mistake into a guardrail so no coding agent makes it twice. Names the class of mistake, picks the strongest affordable enforcement (types, lint rules, architecture tests, Contract tests, CI checks, agent hooks, and written rules only as a last resort), proves it catches the original mistake, and logs it for the team. Use when an agent or person made a mistake that was caught in review, CI, production, or by the user, when the same review comment keeps recurring, when the user says never do that again or always do X, or after an incident or postmortem.
---

# Guardrails: no mistake twice

A guardrail is software, and building one is programming. Prose asks an agent to behave; a guardrail makes the wrong thing fail. Think of bumpers in a bowling lane: the pins are business value, and the ball is whatever the agent does with a prompt.

## 1. Name the mistake and its class

State what went wrong, how it was caught, and how late. Then generalize one level: not "used a float for this price" but "money represented as floating point".

## 2. Pick the strongest affordable enforcement

Work down this ladder and stop at the first practical rung:

| Rung | Mechanism | Examples |
|---|---|---|
| 1. Make it impossible | Types, API shape, schemas, generators | A `Money` type in integer minor units; delete the unsafe helper; a database constraint; code generated from the schema |
| 2. Fail the build | Lint rules, static analysis, architecture tests | `no-restricted-imports`, a Semgrep or ast-grep rule, SwiftLint `custom_rules`, detekt, RuboCop, ArchUnit, dependency-cruiser |
| 3. Fail a test | A Contract obligation and its test, a property test, the mutation gate | An obligation that pins the invariant (`imp-contract`) |
| 4. Fail the merge | A CI check, a PR check, CODEOWNERS | A CI script that rejects the pattern; required owners for `contract/` |
| 5. Catch it at agent time | Agent hooks, skills | A hook that runs the linter after every edit or blocks a dangerous command; a fix to the skill that led the agent astray |
| 6. Write it down | A line in AGENTS.md or an agent rule | Last resort, for judgment no machine can check; note what would mechanize it |

Prefer rungs that protect every person and every agent, not just this session. A rule only you load protects only you.

## 3. Build it like code

- Prove it catches the original mistake: a failing example the guardrail rejects.
- Prove it allows correct code: a passing example it accepts.
- Make the failure message actionable: say what to do instead, and link the log entry.
- Run it across the codebase, and fix or explicitly allow existing violations in the same PR.

## 4. Log it and share it

Append to the guardrails log (default `docs/guardrails.md`):

```markdown
## YYYY-MM-DD: <class of mistake>
- What happened: <one line, with a link>
- Guardrail: <mechanism and where it lives>
- Proof: <the failing example it rejects; the passing example it accepts>
```

Post a one-line summary in the team space: what one person learns, everyone should learn. If the guardrail would help other repos, propose it for the shared lint configuration or the IMP skills.
