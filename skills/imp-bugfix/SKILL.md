---
name: imp-bugfix
description: Handles defects the IMP way. Decides whether the work is a fix (a defect in code live in production) or a refinement; for a real fix, writes the missing Contract obligation, makes it executable, proves the new test catches the bug, and only then fixes the code, so every bug leaves the Contract stronger. Use when fixing a bug, defect, regression, incident, or hotfix in an IMP repo, when labeling work as fix or refinement, or when the user asks how to count or measure bugs honestly.
---

# Every bug leaves the Contract stronger

## 1. Fix or refinement?

A fix repairs a defect in code that is live in production. Everything else is refinement.

- **Live in production:** users hit it, or the commit that introduced it is in a production release. Check with `git tag --contains <sha>`, the deploy history, or the app store version.
- **Not live:** found in review, a preview, staging, or unreleased work. That is a refinement: handle it through `imp-breathe`, label it `refinement`, and don't call it a bug in PRs, tickets, or briefs.
- A dozen small PRs polishing unreleased work are a dozen refinements, not a dozen bug fixes.

If users are being harmed right now, roll back first (`imp-ship`, step 5), then continue here.

## 2. Find what the Contract was missing

A production bug means the Contract was missing something. Decide what:

| Finding | Contract change |
|---|---|
| No obligation covered this behavior | Add one |
| An obligation existed, but no test enforced it | Make it executable |
| A test existed, but didn't catch the bug | Strengthen the test; a surviving mutant usually shows how |
| The obligation itself was wrong | Correct it, after confirming the intended behavior with the customer |

Write the obligation in observable terms at the component's boundary (`imp-contract`).

## 3. Make it executable, and watch it fail

- Write the test through the public boundary, named with the obligation ID.
- Run it against the current code. It must fail, and fail on the assertion about the obligation, not on setup. Keep the output.
- If it passes, the obligation is not what broke. Go back to step 2.
- Never bend the test until it fails. A test massaged into failing fails for an invented reason.

## 4. Fix the code

Make the smallest change that turns the test green, then run the full suite and the contract check. Then breathe out (`imp-breathe`): if this bug has siblings elsewhere, fix the class, not just the instance.

## 5. Guardrail it

If an agent introduced the defect, or the same kind of defect has happened before, run `imp-guardrail` so it can't happen again.

## 6. Ship it as a fix

- Label the PR `fix`, and link the production evidence: incident, ticket, error report, or release.
- In the PR, show the obligation added or strengthened, the failing output, and the passing output.
- A `fix` PR always changes the Contract or its tests. If yours doesn't, it isn't done.
- Ship through `imp-ship`.
