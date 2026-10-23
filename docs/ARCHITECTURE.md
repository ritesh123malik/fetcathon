# Architecture and invariants

## Boundaries

The web API and ACP adapters both call `SupplyService`. The service owns transaction
boundaries, ownership checks, quote state, inventory changes, and receipts. The planner
is a pure function of validated requirements and supplier snapshots. It never calls an
LLM or external service.

ASI:One converts natural language to a bounded request schema. Structured cards bypass
language extraction. The frontend is an operations surface; ASI:One is the primary
hackathon user surface. No custom frontend is required to complete a chat order.

Three supplier uAgents answer typed `InventoryRequest` messages from the coordinator.
The runtime collects responses concurrently with a 12-second timeout. Missing suppliers
are excluded, never fabricated. Every commitment rechecks the authoritative database.
The suppliers currently share a database and deployment, while retaining separate agent
identities and message handlers. They are not independent real-world merchants.

## State transitions

- New request → `quoted` or `unavailable`.
- `quoted` → `confirmed` after all stock and offer checks pass.
- `quoted` → `superseded` if availability changed or the quote expired. A linked quote
  is created; the user must review and approve the new quote.
- `confirmed` → `cancelled`, returning all quantities once.
- A repeated successful confirmation returns the existing order. A different option
  cannot replace an already confirmed order. A cancelled order cannot be resurrected.

Quotes do not hold stock. The reservation happens atomically at approval. That design
avoids abandoned holds and makes competition for the last unit explicit. This is not a
distributed two-phase commit or an escrow system.

## Persistence and concurrency

SQLite WAL supports concurrent readers. `BEGIN IMMEDIATE` serializes inventory mutations.
All line items are checked before any deduction. Every order has a unique `quote_id`;
each transaction creates its receipt and audit event alongside inventory changes.
Database connections are explicitly closed. Seeds use `INSERT OR IGNORE`, so restarts
do not replenish already consumed stock.

The schema is versioned at 1. Future changes require an explicit, tested migration and
backup; do not silently edit existing columns and expect initialization to migrate them.

## Security and truthfulness

- Environment variables hold credentials; the frontend never receives provider keys.
- The public config endpoint exposes booleans and a profile URL only.
- The operations API validates a bearer key with constant-time comparison when configured.
  Local keyless demo mode must stay bound to loopback. Never expose it publicly.
- ACP owner IDs are hashes of sender and session. The operations API has explicitly
  broader authority than chat users and must be protected accordingly.
- Tool parameters and LLM output are validated. Money is recomputed from inventory.
- Planner-mediated confirmations require an explicit action and quote/option identifiers.
- All suppliers are demo businesses; UI and receipts state that no money or real goods move.

## Scaling when justified

1. Replace the database adapter with PostgreSQL and migrations before adding API replicas.
   Use row-level locking or conditional stock updates in one transaction. Preserve the
   concurrency and idempotency regression tests.
2. Introduce authenticated tenant/user identities and role-based operator permissions
   before serving multiple organisations. The current operator key is workspace-wide.
3. For independent supplier services, replace shared commits with expiring reservations,
   idempotent reserve/confirm/release APIs and a durable saga. Network failure cannot be
   solved by a shared SQLite transaction once ownership crosses services.
4. Add a durable job queue, outbox delivery, per-user quotas, tracing, retention and
   service-level monitoring as load and operational requirements demand them.
5. Add payment only with server-side settlement verification, amount/currency/recipient
   binding, replay prevention and explicit refund handling. `CancelPayment` is not a refund.

Current allocation enumerates subsets of three suppliers. It is intentionally bounded;
large catalogues require a different optimisation algorithm, not an unbounded extension
of the same subset enumeration.
