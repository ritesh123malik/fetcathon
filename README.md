# SupplyRescue

**Your backup plan, handled.** Emergency stationery sourcing for campus organisers:
compare supplier offers, approve a plan, reserve inventory, and recover from supplier
failure without committing a partial order.

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

## Two interfaces, one transaction engine

- **ASI:One:** the complete primary workflow through Agent Chat Protocol, interactive
  request forms, option carousels, review cards, receipts, status, and cancellation.
- **Operations UI:** a responsive React dashboard to create requests, inspect orders,
  update inventory, pause suppliers, and demonstrate failure recovery.

The coordinator exchanges typed uAgent messages with six supplier identities.
Suppliers return their inventory snapshots; the planner computes feasible allocations.
ASI:One interprets natural-language requests. Prices, budgets, stock checks, and order
commits are deterministic Python code.

## Public agent

- Name: **SupplyRescue Campus Recovery** (runtime display name: SupplyRescue)
- Address: `agent1qvftq6nwwq7wpl9wd3g70mtyflktwy73afld2tjmqv0uvynrg0d0jcyfg4t`
- [Agentverse profile](https://agentverse.ai/agents/details/agent1qvftq6nwwq7wpl9wd3g70mtyflktwy73afld2tjmqv0uvynrg0d0jcyfg4t/profile)
- [GitHub repository](https://github.com/ritesh123malik/fetcathon)

Registration alone does not establish uptime: an agent worker must be online. See
[deployment](docs/DEPLOYMENT.md) and the [submission checklist](docs/SUBMISSION.md).

## Quick start

Requires Python 3.11–3.13, Node.js 22+, npm, and uv. The dependency lockfiles are committed.

```bash
cp .env.example .env
uv sync --python 3.11
cd frontend
npm ci
npm run build
cd ..
uv run uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. Demo mode seeds six fictitious suppliers exactly once.
Restarting the service preserves orders and inventory. No API key is required for the
structured form or labelled offline parser. To use real ASI:One intent extraction,
set `ASI_ONE_API_KEY` in `.env` and restart the process.

For frontend development, run `make api` and `make web` in separate terminals. Vite
proxies `/api` to the Python service. Open the Vite URL printed in its terminal.

## Run the ASI:One agent network

For the configured laptop demo, after building the frontend and setting up `.env`,
run `make demo` to start both the local dashboard and the agent network. On macOS,
use `caffeinate -i make demo` to prevent idle sleep while it runs. Keep the laptop
plugged in, its lid open and internet connected. Stop with Ctrl+C. See the
[laptop demo guide](docs/DEPLOYMENT.md#laptop--mailbox-demo-no-cloud-hosting-fee).

Set a strong, stable `AGENT_SEED` and your `AGENTVERSE_API_KEY` in `.env`. For a new
installation generate your own seed; never reuse the published agent's identity.

```bash
uv run python -m scripts.check_connections
uv run python -m scripts.register_agent
uv run python -m agents.runtime
```

Keep the worker running. Mailbox mode retrieves queued messages without a public inbound
agent endpoint. In ASI:One select the agent from its profile and say:

> Find 60 notebooks and 60 pens under INR 4500 within 24 hours.

Select a plan, review its allocation, and confirm. The receipt appears in the same
conversation. Use `orders` to inspect status and `cancel SR-XXXXXXXX` to release an order
owned by that conversation. `start` opens the structured request form.

## Expanded use cases and order tracking

Six demo supplier agents cover workshops, conference registration packs, classroom
restocking and employee onboarding. The catalogue includes notebooks, pens, lanyards,
markers, folders and badges. Send `catalogue` in ASI:One for stock, prices and examples.
The request form has matching example prompts and all six products.

Clarification turns retain request context for up to 24 hours; `start` clears it.
Minutes convert to fractional hours. Infeasible requests explain alternative budgets
and deadlines without making commitments on your behalf.

After confirmation, send `track SR-XXXXXXXX` or open **Orders → Track shipments**.
Each supplier shipment has a reservation reference, estimate, timestamped history and
reserved/packing/dispatched/delivered progress. The panel refreshes every five seconds.
An operator uses explicitly labelled demo buttons to report progress; this is not GPS,
a courier integration or actual delivery. Estimates are flagged overdue, never assumed
delivered. Once any shipment dispatches, automatic cancellation is blocked.

## Reproducible recovery demo

1. Create the sample request above. With untouched seed inventory the best-value plan is
   **INR 2,720** across Campus Paper Co. and Metro Office Supply.
2. Close the review panel without confirming. In Supplier network, pause Campus Paper Co.
3. Reopen the quote and confirm it. The engine detects changed availability and commits
   **nothing**. It proposes a replacement requiring fresh approval.
4. The replacement costs **INR 3,120** from Metro Office Supply with untouched seed stock.
5. Approve it. Inspect the reservation IDs and reduced available stock.
6. Cancel the order; stock is released once, even if cancellation is retried.
7. Resume Campus Paper Co. before another demo. Prior orders can change example prices.

For the official primary-workflow demonstration, perform steps 1, 3–6 in ASI:One. Supplier
disruption is an operator action, not a required end-user frontend interaction.

## Verification

```bash
uv run pytest -q
uv run ruff check backend agents scripts tests
uv run ruff format --check backend agents scripts tests
uv run python -m scripts.smoke_agent_network
cd frontend
npm run build
npx prettier --check src e2e
# With an isolated demo API running on port 8000:
npm run test:e2e
```

The network smoke test exchanges real messages between uAgents and walks the carousel →
review → receipt flow using a temporary database. It disables external registration.
Browser tests exercise recovery, cancellation and mobile layout; they modify demo data
and should run against an isolated demo instance, not a shared deployment.

## Structure

```text
backend/            FastAPI adapters, validated models, intent extraction
  service.py        Transaction and ownership invariants
  planner.py        Deterministic bounded allocation
  db.py             SQLite schema, connection lifecycle and transactions
agents/             Native ACP cards, conversation workflow and uAgent runtime
frontend/src/       Typed React operations UI
tests/              Transaction, isolation, API and chat regression tests
scripts/            Registration, connectivity, process supervision, network test
docs/               Architecture, deployment and submission material
```

## Guarantees and limits

- Integer paise for money; complete quantities and budgets are validated before approval.
- `BEGIN IMMEDIATE`, stock constraints and unique quote/order linkage prevent overselling
  and duplicate fulfilment across retries or concurrent confirmations.
- Ten-minute quotes are revalidated at commit. Recovery always asks for new approval.
- Agent conversations cannot read or cancel other conversations' records.
- The authenticated operations dashboard can administer all workspace records.
- Demo suppliers are fictitious. Reservations update persistent inventory but do not
  purchase real products, collect payment, or dispatch delivery.
- Supplier fulfilment times are fixtures. The catalogue is notebooks, pens and lanyards.
- Payment Protocol is intentionally not implemented or claimed. A payment message without
  settlement verification would not be a credible monetisation implementation.
- This is a single-instance deployment with a shared SQLite authority. It is modular,
  but not a horizontally scaled distributed merchant marketplace. See the documented
  [scaling path](docs/ARCHITECTURE.md).

Never publish `.env`, agent seeds, wallets, database files, or private conversation logs.
Public deployments must set `ADMIN_API_KEY`; the Render blueprint generates one.
