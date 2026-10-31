---
name: impatient-programming
description: Operating manual for Impatient Programming (IMP), an AI-era successor to eXtreme Programming. Defines the IMP virtues, vocabulary, and lifecycle (weekly story, spikes, Contract-first pull requests that inhale and exhale, behavior-focused tests, optional mutation audits, green-merges-itself shipping, weekly showcase) and routes to the imp-* skills. Use when working in a repository whose AGENTS.md or CLAUDE.md has an Impatient Programming section, when the user mentions IMP, Impatient Programming, imps, or the Contract, or when deciding how a team should plan, build, test, review, or ship software with coding agents.
---

# Impatient Programming (IMP)

IMP takes what worked in eXtreme Programming and turns the dials up for teams whose programmers pair with coding agents all day. Speed is a core value. What keeps speed honest is rigor that runs in machines: executable Contracts, fast behavioral tests, merge checks, and guardrails on every change. Mutation testing is a targeted, optional diagnostic; complete kill matrices are deliberate non-blocking audits. The agent is the pair: it talks decisions through, challenges the plan, and keeps the Contract while the human steers.

Based on Obie Fernandez's [eXtreme Programming, Revisited](https://impatientprogramming.org/xp-revisited/).

## Virtues

- **Impatience, kept honest by feedback.** Ship as much as possible, as quickly as possible. Every merge is released, and the customer sees the work this week. Zero tolerance for technical debt: a known-wrong shape does not live another day.
- **Laziness, kept honest by simplicity.** Put the effort into guardrails so no agent makes the same mistake twice. Prefer convention over configuration and expressive code.
- **Hubris, kept honest by courage and respect.** Boil the lake: once you know what to build, build it complete and tight, in a codebase as close to architectural perfection as possible. Your mess must never derail a teammate.
- XP's values carry over untouched: communication, simplicity, feedback, courage, respect. Above them all, people first. It is always a people problem, and when the team wins, it is because of the people.

## Vocabulary

Use these terms exactly, without synonyms.

| Term | Meaning |
|---|---|
| Contract | The versioned, in-repo description of what the software must do, functional and non-functional, written as numbered obligations. The thing most worth protecting, and the main focus of review. |
| Obligation | One numbered promise in the Contract, such as `QUO-004`. Executable when a test whose name carries its ID enforces it. |
| Inhale | The exploratory half of a PR: the agent sprawls until the feature reveals what it wants to be, recording obligations as they are agreed. |
| Exhale | The consolidating half of the same PR: fold what was learned back into what already exists, delete what is not needed, complete the Contract. |
| Spike | A throwaway experiment that answers one question. Cheap, parallel, never merged. A bakeoff compares spikes on the same measures. |
| Boil the lake | Build it complete once you know what to build. Completeness is now cheaper than shortcuts. |
| Kill matrix | A diagnostic mapping of injected mutants to tests that detect them. A complete matrix is optional audit evidence, never the sole basis for test deletion or a mandatory PR gate. |
| Fix | A change that repairs a defect in code that is live in production. |
| Refinement | Every change that is not a fix, labeled that way. |
| Blast radius | How much can go wrong if a change is bad: low, medium, high, or catastrophic. It decides how much human review a PR gets. |
| Green merges itself | When automated checks and an adversarial model review pass, the PR merges and releases without waiting for a human, within the team's blast-radius policy. |
| Guardrail | Software that stops an agent from repeating a mistake: a type, lint rule, test, check, or hook. |
| Regeneration drill | Rebuilding a component from its Contract, decision records, and interfaces alone, without the old code, to prove the Contract is complete. |
| Story | The week's success criteria, posted where the team can see them. Not a user story. |
| Hill | A long project's position: uphill while unknowns are still being turned into knowns (no date), over the top once the person who committed can give a forecast they believe. |
| Showcase | The weekly demo where only finished work counts, and product is shown in production. |
| Team space | The public channel where people and agents work in the open. |

## The flow

Work flows pull request by pull request. There are no iterations to plan against, only a weekly heartbeat.

1. **Get the story straight.** Before committing to work for the week, write success criteria and post them. Use `imp-heartbeat`.
2. **Start with artifacts and experiments.** Talk the design through in an editable artifact, look at three options, name hypotheses, run parallel spikes, and put prototypes in front of the customer. Use `imp-spike`.
3. **Inhale.** Build, letting the agent sprawl. Write each obligation into the Contract the moment it is agreed. Use `imp-breathe` and `imp-contract`.
4. **Exhale.** In the same PR, fold the new code back into the system, delete the excess, complete and execute the Contract, and make every test earn its place with meaningful behavioral assertions. Use `imp-breathe`; use `imp-kill-matrix` selectively for diagnostics.
5. **Ship.** Size the blast radius, run checks and an adversarial review, let green merge itself where policy allows, release every merge, watch it, and roll back fast. Use `imp-ship`.
6. **Work in the open.** Post a daily brief of what you and your agents did, and hold a weekly showcase of finished work only. Use `imp-heartbeat`.

Side loops:

- A defect in production goes through `imp-bugfix`: the Contract was missing something, so strengthen it before fixing the code.
- Any mistake an agent made, whether caught in review, CI, production, or by the user, goes through `imp-guardrail`.
- Important components get periodic `imp-regen-drill` runs.
- A repo new to IMP starts with `imp-init`.

## Rules for agents in an IMP repo

1. **Read the Contract before the code.** Read as little code as the task allows.
2. **Contract first.** A change that alters behavior alters the Contract in the same PR. Record an obligation when it is agreed, not at the end.
3. **Every PR breathes.** No PR ships without its exhale.
4. **No debt.** Add no TODO, FIXME, or temporary code. A known-wrong shape in code you touch gets fixed now, or in the very next PR.
5. **Three options, not one.** When a design choice is open, present three real options with trade-offs before building one. Prefer an experiment to a guess.
6. **Tests earn their place.** Keep tests that protect distinct behavior, obligations, regressions, boundaries, and failure cases; remove duplication on evidence, not mutation score alone. Never require a full kill matrix in PR CI.
7. **Label honestly.** `fix` only for defects live in production; everything else is `refinement`.
8. **No mistake twice.** When you or another agent get something wrong, add a guardrail, not only a correction.
9. **Respect the merge policy.** Green merges itself only within the repo's blast-radius policy. Never bypass branch protection, required reviews, or failing checks, and never approve your own PR.
10. **Every merge is released**, directly or behind a flag, with a known rollback.
11. **Learn in public.** Lessons go into the repo (Contract, decision records, guardrails log, AGENTS.md) or the team space, never only into a private chat.
12. **People first.** Humans decide product questions. Credit people for their work. Be kind in reviews and briefs.

## Repo facts

An IMP repo declares its facts in an `## Impatient Programming` section of `AGENTS.md` (or `CLAUDE.md`), which `imp-init` writes. Read it first. Where a fact is missing, use the default:

| Fact | Default |
|---|---|
| Contract | `contract/`: `README.md` is the system Contract, `<component>.md` one file per component |
| Contract tests | A `contract` folder in the test tree; each test name carries its obligation ID |
| Decision records | `docs/decisions/NNNN-title.md` |
| Guardrails log | `docs/guardrails.md` |
| Change labels | `fix`, `refinement` |
| Mutation policy | Optional, scoped, time-budgeted probes; full matrices only in non-blocking scheduled/manual audits |
| Merge policy | The default table in `imp-ship` |
| Release | Every merge to the default branch reaches production, directly or behind a flag |
| Team space | None: print briefs in chat for the user to post |

If the repo has no IMP section and the user wants to work this way, run `imp-init` first.
