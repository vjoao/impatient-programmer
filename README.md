# Impatient Programming skills

Agent skills that make coding agents in Cursor and Codex work the Impatient Programming way. Impatient Programming (IMP) is Obie Fernandez's AI-era successor to eXtreme Programming, set out in his essay [eXtreme Programming, Revisited](https://impatientprogramming.org/xp-revisited/). These skills turn the method into steps a coding agent follows and checks that run on every change.

This is an independent adaptation, not affiliated with or endorsed by Obie Fernandez or ZAR. Read the essay for the method and the reasoning behind it.

## Impatient Programming in brief

XP took practices that worked and turned them up as far as they would go. IMP does the same for teams whose programmers pair with coding agents all day. Speed is a core value, and what keeps it honest is rigor that runs in machines: executable Contracts, mutation gates, merge checks, and guardrails.

- **The Contract.** Each repo keeps a versioned description of what the software must do, written as numbered obligations, functional and non-functional. It is the main focus of review, and it should be complete enough to rebuild any component from it.
- **Every pull request breathes.** On the inhale, the agent explores and builds freely, writing each obligation into the Contract as it is agreed. On the exhale, in the same pull request, it folds the new code into what already exists, deletes what isn't needed, and completes the Contract. No technical debt survives the exhale.
- **Tests earn their place.** Mutation testing shows which tests catch which injected bugs. A test stays only if it catches something no other test catches.
- **Green merges itself.** When the checks and an adversarial review by a second model pass, a pull request merges and is released without waiting for a person, as far as the team's policy allows for its blast radius (how much could go wrong). Every merge is released, behind a canary or flag when needed, with a known rollback.
- **No mistake twice.** A mistake an agent made becomes a guardrail: a type, lint rule, test, check, or hook that stops it from happening again.
- **A weekly heartbeat instead of iterations.** Work flows pull request by pull request. Each week starts with posted success criteria, a daily public brief says what people and their agents did, and a weekly showcase counts only finished work in production. Long projects report whether they are still uphill, turning unknowns into knowns, or over the top with a forecast someone believes.

## What this repo contains

- An operating manual, the `impatient-programming` skill, with the vocabulary, the flow, and rules for agents. Agents pick it up in any repo whose `AGENTS.md` or `CLAUDE.md` has an Impatient Programming section, and it sends them to the right step.
- One skill for each step of the cycle, each a procedure the agent follows.
- Three scripts for the mechanical checks, which also run in CI.
- A setup skill, `imp-init`, that adds the Impatient Programming section and supporting files to a repo, so every agent working there, and CI, follows the method.

### Skills

| Skill | What it does |
|---|---|
| `impatient-programming` | Operating manual: virtues, vocabulary, the flow, rules for agents, and default repo settings. Routes to the other skills. |
| `imp-init` | Makes a repo ready: the `AGENTS.md` section, a system Contract, a first decision record, a guardrails log, PR template sections, `fix` and `refinement` labels, and a CI job. Asks before any change outside the repo. |
| `imp-spike` | Before production code: three real options, named hypotheses, parallel throwaway spikes and bakeoffs, prototypes for the customer, and a decision record. |
| `imp-contract` | Writes and checks the Contract: obligation format, permanent IDs, templates, a checklist of what to ask, and tests that carry obligation IDs. |
| `imp-breathe` | The inhale and exhale of each pull request, with the exhale checklist and the PR description sections. |
| `imp-kill-matrix` | Sets up mutation testing for the stack, builds the kill matrix, and says which tests to delete or strengthen and what each surviving mutant means. |
| `imp-ship` | Sizes the blast radius, runs checks and an adversarial review by a different model, applies the merge policy, and handles rollout, watching, and rollback. |
| `imp-bugfix` | Decides whether work is a fix (a defect live in production) or a refinement. For a fix, adds the missing obligation and a failing test before changing code. |
| `imp-guardrail` | Turns a mistake into the strongest affordable automated check, proves it catches the mistake, and logs it. |
| `imp-regen-drill` | Rebuilds a component from its Contract alone, in a copy without history, to find gaps in the Contract and weak tests. |
| `imp-heartbeat` | The week's story, the daily brief, and the weekly showcase. |

### Scripts

The scripts are standard-library Python 3.8 or later, with nothing to install. They live inside the skills, and `imp-init` copies them into a repo's `scripts/imp/` folder so CI doesn't depend on anyone's skill install.

- **`check_contract.py`** (in `imp-contract`) checks obligation format and unique IDs, finds the tests that cite each obligation, and reports obligations no test covers. With `--strict` it fails on them.
- **`kill_matrix.py`** (in `imp-kill-matrix`) reads a Stryker JSON, PIT XML, or CSV mutation report. It reports the mutation score, surviving mutants, redundant tests, tests that kill nothing, and tests it protects because they are the only test of an obligation. When the report lists only the first test to kill each mutant, it withholds deletion advice, because acting on it would delete good tests.
- **`blast_radius.py`** (in `imp-ship`) rates the current change low, medium, high, or catastrophic from the paths it touches, what it adds (secrets, destructive migrations), its size, and the obligations it changes or retires. It prints the review gate that level requires.

```console
$ python3 scripts/imp/blast_radius.py --base main
Blast radius: catastrophic (a floor: raise it if the code's meaning warrants; only a human may lower it)
Base: main (merge base 405b921a6a), 4 files, +9 -5 lines

  catastrophic  db/migrate/001_drop_email.rb:1  destructive data change: remove_column
  high          contract                        obligations retired: QUO-003
  high          db/migrate/001_drop_email.rb    database migration or schema
  high          src/auth/login.ts               authentication, authorization, or security
  medium        contract                        obligations changed: QUO-002
  medium        package.json                    dependencies
  low           1 docs, test, or team low-risk files

Contract: added QUO-004; changed QUO-002; retired QUO-003

Default gate: A human reviews code, Contract, and rollout; rehearse the rollback; never auto-merge.
```

## Install

You need git, and Python 3.8 or later for the scripts. The GitHub CLI (`gh`) is optional; `imp-init` and `imp-ship` use it for labels and auto-merge. Mutation testing needs a tool for your stack; [tools.md](skills/imp-kill-matrix/tools.md) covers the common ones.

From a clone of this repo, link the skills:

```sh
scripts/link-skills.sh
```

This links each skill folder into `~/.agents/skills`, which both Cursor and Codex read, so they load the skills straight from the repo. Run it again after adding a skill. It never replaces a real folder with the same name. If you move or delete the repo, the links break.

Keep the links in one folder where you can. Cursor also reads `~/.cursor/skills`, `~/.claude/skills`, and `~/.codex/skills`, and depending on its version it may list a skill found in two of them twice. Claude Code reads `~/.claude/skills`, so link there for it: `scripts/link-skills.sh ~/.claude/skills`. The skills have been tested in Cursor, not yet in Codex or Claude Code.

The repo is also a Cursor plugin (`.cursor-plugin/plugin.json`), so it can be shared later through a team or public Cursor marketplace. If you install it that way, remove the links first, or every skill will be loaded twice.

## Use

1. Open a project and run `/imp-init` in Cursor, or `$imp-init` in Codex. It reads the repo, asks one round of questions (the system's name and metaphor, where the team posts updates, the merge policy, how a merge reaches production, and who the customer is), shows its plan, and writes only what's missing.
2. Then work as usual. The agent follows the cycle by itself. These prompts start each part of it:
   - "Post this week's story."
   - "Give me three options for <decision>." or "Spike <A> and <B>."
   - "Add <feature>." The agent inhales and exhales in the same pull request.
   - "Ship this PR."
   - "Write today's brief." and, at the end of the week, "Prepare the showcase."
   - "This is broken in production: <what happened>."
   - "Guardrail this." after an agent gets something wrong.
   - "Run the kill matrix on <module>." and "Run a regeneration drill on <component>." every so often.
3. To run a skill directly, type `/` and its name in Cursor, such as `/imp-ship`, or `$imp-ship` in Codex, where `/skills` lists them.

You make the product decisions, confirm or reject the obligations the agent proposes, and read the Contract diff first when reviewing a pull request. The agent keeps the Contract current, writes and prunes tests, runs the scripts, and drafts the updates.

### In Codex

The skills and scripts are the same in Codex, but a few things behave differently:

- Codex reads every `AGENTS.md` from the repo root down to the folder you start it in, so the section `imp-init` writes applies as is.
- Restart Codex after editing a skill. It doesn't notice changes made through the links while it's running.
- The adversarial review in `imp-ship` and the rebuilds in `imp-regen-drill` need agents that start with no conversation history. A Codex subagent can start as a fork of the current conversation, so the skills ask for an empty one or a separate `codex exec` session. Codex subagents also use the same model unless you ask for another, and all of Codex's models come from OpenAI, so the review is less independent than one by another vendor's model.
- By default Codex asks before writing outside the project folder or using the network. Expect approval prompts for `gh` commands, pushes, and spikes, which create worktrees next to the repo.
- To post the daily brief on a schedule, use a CI cron job rather than a Cursor Automation.

### What `imp-init` adds to a repo

```text
AGENTS.md                           Impatient Programming section with the repo's settings
contract/README.md                  system Contract; one <component>.md per component
docs/decisions/0001-adopt-impatient-programming.md
docs/guardrails.md                  every mistake made once, and what now prevents it
.github/pull_request_template.md    Story, Change type, Contract, Breath, Evidence, Blast radius
scripts/imp/                        copies of the three scripts, so CI doesn't need the skills
```

It also adds a GitHub Actions job that checks the Contract, reports the blast radius, and runs a mutation gate. Settings that differ from the defaults, such as the Contract folder, the merge policy, or risky paths, go in the repo's `AGENTS.md` section rather than in the skills.

An obligation in the Contract looks like this:

```markdown
### QUO-002 [latency] Quotes return inside the checkout timeout
The quote service shall respond within 120 ms at p99 at 50 requests per second.
Why: checkout calls it with a 150 ms timeout; slower responses surface as intermittent checkout failures.
```

A test enforces it by carrying its ID in its name, such as `test_quo_002_responds_within_120_ms`. Statements follow EARS ("When ..., the ... shall ..."), so each one is a single testable promise.

### Merging stays under your control

Green merges itself only as far as the repo's policy allows. The agent never bypasses branch protection, required reviews, or failing checks, and never approves its own pull request. The default policy:

| Blast radius | Gate before merge |
|---|---|
| low | Green checks and a clean adversarial review, then auto-merge |
| medium | As low, plus release behind a canary or flag; a person reads the Contract diff if obligations changed |
| high | A person reviews the Contract diff and the rollout plan |
| catastrophic | A person reviews code, Contract, and rollout; the rollback is rehearsed; never auto-merged |

## Repository layout

```text
.cursor-plugin/plugin.json   plugin manifest
skills/<name>/SKILL.md       one folder per skill, with its templates and scripts
scripts/link-skills.sh       links the skills into ~/.agents/skills, or another folder
```

## Credits

Impatient Programming is the work of **Obie Fernandez**, who set it out in [eXtreme Programming, Revisited](https://impatientprogramming.org/xp-revisited/). It was born at ZAR, where he is CTO, from practices he and his colleagues developed and use every day, and he thanks **Stephen Margheim**, **Brandon Timinsky**, and **Sebastian Scholl** by name. The method, its vocabulary, and its rules are theirs. This repo adapts them into agent skills, and any mistakes in the adaptation are its own.

The essay's liner notes credit the people whose ideas IMP builds on:

- **Kent Beck, Ward Cunningham, Ron Jeffries, and Don Wells**, who drew the first map with eXtreme Programming.
- **Larry Wall**, who named the three virtues, laziness, impatience, and hubris, in *Programming Perl*.
- **Gerald Weinberg**, who taught that it's always a people problem.
- **Peter Naur**, who saw the theory behind the code (*Programming as Theory Building*).
- **Ryan Singer**, whose *Shape Up* gave IMP the hill.
- **Garry Tan**, who boils lakes and oceans.
- **Eric Ries**, who taught a generation to experiment (*The Lean Startup*).
- **C. Northcote Parkinson**, who explained why deadlines expand (Parkinson's law).
- **Chad Fowler**, who named regenerative software.
- **Frank Westphal**, who first mapped XP onto AI.

The skills also build on:

- **EARS**, the Easy Approach to Requirements Syntax, by Alistair Mavin and colleagues at Rolls-Royce, for obligation statements.
- **Stryker** and **PIT**, whose mutation reports `kill_matrix.py` reads, including Stryker's open mutation-testing report schema.

Adapted into agent skills by Victor Nascimento.
