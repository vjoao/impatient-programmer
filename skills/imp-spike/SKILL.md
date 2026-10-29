---
name: imp-spike
description: Starts work the IMP way, before production code. Talks the design through in an editable artifact, offers three real options, names hypotheses and assumptions, runs parallel throwaway spikes and bakeoffs, puts prototypes in front of the customer, and records the outcome as a decision record and Contract obligations. Use when starting a feature or project, when the right approach or what the customer wants is unclear, when comparing designs, libraries, or architectures, when prototyping screens, or when the user mentions spikes, bakeoffs, experiments, prototypes, trial balloons, or options.
---

# Spike: experiment on what to build

Stop guessing. Experiments cost minutes now, so run them before committing to a design, run several at once, and let the results argue it out.

## 1. Start with an artifact

Open an editable artifact the user can see and change: a markdown doc in the repo (`docs/shaping/<topic>.md`), a canvas, or design frames for UI. Talk through the design and architecture decisions in it until you both understand what is being built.

- First make a quick comp, a strawman to react to, and expect it to be rejected.
- Then offer three genuinely different options, each with its trade-offs, its cost, and what it would make hard later. Not three variations of one idea.
- Record each decision the user makes in the artifact.

## 2. Name hypotheses and assumptions

Write them in the artifact:

- **Hypotheses:** "We believe <change> will <outcome>. We will know when <observable signal>."
- **Assumptions:** what must be true for the plan to work, about users, data, dependencies, or performance. Rank them by risk and uncertainty, and test the riskiest first.

## 3. Run spikes in parallel

A spike answers one question, takes minutes, and is thrown away.

- Before starting each spike, write its question and how its answer will be judged.
- Run spikes in parallel, each in its own branch and worktree (`git worktree add ../<repo>-spike-<name> -b spike/<name>`), ideally as parallel subagents.
- In a bakeoff, give every contender the same task and score them on the same measures: correctness against the draft obligations, latency, code size, dependency weight, user experience.
- Each spike reports its answer, its evidence (numbers, screenshots, links), and its surprises. Then delete its worktree and branch. Spike code is never merged.

## 4. Put it in front of the customer

The customer (product owner, stakeholder, or user) sees a prototype early, not a document:

- Throwaway prototypes, trial balloons, several versions of a screen at once: a preview deploy, a static page, a Storybook story, or design frames.
- Ask what they would change, then iterate. Record their reactions in the artifact.
- If the customer built a prototype themselves, treat it as the richest spec available: extract its behavior into obligations, and don't productionize its code.

## 5. Decide, record, and unleash

1. Write a decision record in the repo's decision folder (default `docs/decisions/NNNN-<title>.md`) using the template below.
2. Seed the Contract with every obligation the experiments settled (`imp-contract`).
3. Then unleash the build and boil the lake, through `imp-breathe`.

```markdown
# NNNN. <Decision title>

Date: YYYY-MM-DD · Status: accepted · Decided by: <names>

## Context
The question we needed to answer, and why now.

## Hypotheses and assumptions

## Options
At least three, each with its trade-offs.

## Evidence
Spikes, bakeoff scores, and customer reactions, with links.

## Decision

## Consequences
What becomes easier or harder. Contract obligations added: <IDs>.
```
