---
name: imp-heartbeat
description: Runs the IMP team heartbeat. Opens the week by getting the story straight (success criteria posted publicly, plus hill position and forecast for long projects), writes the daily public brief of what people and their agents did in the last 24 hours, and prepares the weekly showcase of finished, in-production work only. Use when planning or committing to a week's work, writing success criteria, forecasting a long project, writing a daily brief, standup, or status update, or preparing a showcase or demo.
---

# Heartbeat: story, brief, showcase

IMP has no iterations. Work flows PR by PR, with a weekly heartbeat: the story opens the week, the showcase closes it, and a public brief every morning keeps the work in the open.

Post to the team space named in the repo's facts (Confluence, Slack, GitHub Discussions, or a file in the repo) through whatever integration is available. When a person is in the session, show them the draft before posting; unattended runs post directly. With no integration, print the text for the user to paste.

## Get your story straight (the week opens)

Before committing to a project for the week, write its success criteria and post them.

- Someone else must be able to check each criterion at the end of the week: "Quote caching is live in production in all markets", "The customer chose one of three onboarding prototypes". Activities like "work on caching" are not criteria.
- Link the Contract components and decision records involved.
- For a long project, give its position on the hill:
  - **Uphill:** still turning unknowns into knowns. List the open unknowns and the next spike for each. Give no date.
  - **Over the top:** whoever committed gives a forecast they believe, and what would change it. A forecast, not a deadline.

```markdown
**Story: week of <date>, <person or team>**
Success criteria:
1. <criterion>
Hill: <project> is uphill (unknowns: ...; next spikes: ...) | over the top (forecast: ...; risks: ...)
```

## Daily brief (every morning)

What you and your agents did in the last 24 hours, in public. Gather it rather than recalling it:

- `git log --since="24 hours ago" --author=<me>` across the active repos; merged PRs (`gh pr list --state merged --search "merged:>=<date>"`); releases and deploys; obligations added to the Contract; guardrails added; spikes and their answers; drills.
- Tickets that moved, if the tracker is connected.

```markdown
**Brief: <date>, <person> and agents**
Shipped: <PRs merged and released, one line each, with links>
Learned: <spike answers, Contract additions, guardrails>
Next: <today's focus, tied to this week's criteria>
Blocked: <anything, and who can help>
Fixes: <n> production defects · Refinements: <m>
```

Keep it under 15 lines. To post it every morning unattended, schedule it as a Cursor Automation, a CI cron job, or similar.

## Showcase (the week closes)

Only finished work counts: merged, released, and, for product, demoed in production.

1. Collect the week's merged PRs, and check that each is in production (deploy history, release tags, flag state). Drop anything not live. Work in progress doesn't appear at all.
2. Map the items to the week's success criteria and mark each criterion met or not met. Be honest: a missed criterion is information, not failure.
3. For each item, give what it is and who it's for, the production link or demo steps, before and after, the obligations it added to the Contract, and the customer's reaction if known.
4. Credit the people involved by name. The showcase exists so people can show their best work and be appreciated for it.

```markdown
**Showcase: week of <date>**
Criteria: 1. <criterion>: met. 2. <criterion>: not met (why, and what's next)
Demos:
- <Title>, for <who>: <production link or steps>, by <names>
Numbers: <n> PRs released · <f> fixes · <r> refinements · <o> obligations added · <g> guardrails added
```
