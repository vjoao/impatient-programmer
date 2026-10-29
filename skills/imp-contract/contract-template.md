# Contract templates

## System Contract: `contract/README.md`

````markdown
# <System name>: Contract

## Metaphor
One paragraph: what this system is, told as the story the team shares. Names in the code come from here.

## Vocabulary
- **<Term>**: <meaning>. In code: `<Identifier>`.

## Components
| Component | Contract | Code | Prefix |
|---|---|---|---|
| Quote service | [quote.md](quote.md) | `src/quote/` | QUO |

## Cross-cutting obligations

### SYS-001 [privacy] Personal data stays out of logs
The system shall not write personal data to logs, traces, or analytics events.
Why: logs are retained longer and seen by more people than the data's consent allows.

## Non-goals
- What the system deliberately does not do.

## Decisions
Decision records live in `docs/decisions/`.
````

## Component Contract: `contract/<component>.md`

````markdown
# <Component>: Contract

Prefix: `QUO` · Code: `src/quote/` · Owners: <team or people> · Last regeneration drill: never

## Intent
Two to four sentences: why this component exists, who calls it, and what it promises them, in the system's vocabulary.

## Interfaces
What it exposes and consumes, by reference to the source of truth: API spec, schema, type definitions, event names.

## Obligations

### QUO-001 [functional] Issued quotes are immutable
When a quote has been issued, the quote service shall reject any change to its amount or currency.

### QUO-002 [latency] Quotes return inside the checkout timeout
The quote service shall respond within 120 ms at p99 at 50 requests per second.
Why: checkout calls it with a 150 ms timeout.

### QUO-003 [observability] Every rejected quote is counted
When the quote service rejects a request, it shall increment the `quote_rejected_total` metric with the rejection reason.
Verified by: manual — checked on the dashboard until the metrics test harness exists.

## Latitude
Choices deliberately left open. A regeneration may decide these freely.
- Internal caching strategy, as long as QUO-002 holds.

## Unconfirmed
Candidate obligations inferred from existing code, waiting for a human to confirm or reject them. Not enforced.

## Open questions
Behavior nobody has decided yet, each with a proposed answer and an owner.
````

## Kinds

Use one kind per obligation: `functional`, `error`, `idempotency`, `ordering`, `consistency`, `concurrency`, `durability`, `latency`, `timeout`, `throughput`, `resource`, `compatibility`, `dependency`, `security`, `privacy`, `accessibility`, `observability`, or `retired`.
