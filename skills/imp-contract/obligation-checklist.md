# Obligation checklist

Walk this list for each component a PR touched. When a caller relies on the answer, write an obligation. When the answer is deliberately open, add it to `## Latitude`. When nobody knows, add it to `## Open questions` and ask.

## Behavior

- **functional:** What does each operation promise its caller, including empty, missing, duplicate, and boundary inputs?
- **error:** What does the caller observe on each failure: error type, code, message shape, partial results?
- **idempotency:** Is each operation safe to retry? What happens on a duplicate request or a redelivered message?
- **ordering:** Does any caller rely on the order of results, events, or side effects?
- **consistency:** After a write returns, when do reads reflect it, and in which components?
- **concurrency:** What happens when two requests touch the same thing at once? Who wins, and what does the loser see?
- **durability:** What survives a crash, restart, or redeploy? What may be lost?

## Time and load

- **latency:** What latency do callers assume, and what are their timeouts? A component that averages 100 ms behind a caller that times out at 150 ms has an obligation, even if nobody wrote it down.
- **timeout:** How long does this component wait on each dependency, and what does it do when one is slow or down?
- **throughput:** What load must it sustain? Past that load, does it queue, shed, or fail?
- **resource:** Which memory, CPU, connection, storage, or cost ceilings must it stay under?

## Boundaries

- **compatibility:** Which API shapes, event schemas, stored data, platforms, and client versions must keep working, and for how long?
- **dependency:** What may it call, and what must it never call directly?
- **security:** Who may call each operation? What must be validated, rate-limited, or audited?
- **privacy:** Which data is personal? Where may it be logged, stored, or sent, and for how long?
- **accessibility:** For UI, which keyboard paths, screen reader labels, contrast, and focus order must hold?
- **observability:** Which logs, metrics, traces, or events do operators, dashboards, and alerts rely on?
