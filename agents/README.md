# SupplyRescue — emergency campus supplies

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)
![tag:domain/shopping](https://img.shields.io/badge/shopping-4CAF50)

SupplyRescue helps campus organisers recover from last-minute stationery shortages.
Compare independent supplier quotes, review a complete allocation, approve inventory
reservations, and receive a receipt entirely inside ASI:One. Supports Agent Chat Protocol
and interactive form, carousel, and review cards.

## Try it

- "Find 60 notebooks and 60 pens under INR 4500 within 24 hours."
- "I need 30 lanyards under INR 1000 within 6 hours."
- "start" opens a guided request form.
- "orders" displays orders in this conversation.
- "catalogue" shows available suppliers, prices, stock and example use cases.
- "track SR-XXXXXXXX" shows per-supplier fulfilment updates and estimated arrival.
- "Find 50 badges, 50 lanyards and 50 folders under INR 5000 within 12 hours."
- "I need 10 markers and 30 notebooks under INR 2500 within 8 hours."
- "cancel SR-XXXXXXXX" releases a reservation you own.

## What happens

The coordinator requests stock snapshots from six supplier uAgents. A deterministic
planner checks quantities, cost, deadline and stock. You review a plan before confirming.
Confirmation revalidates every item and atomically reserves stock. If a supplier changes
availability, a revised quote requires your approval. Retrying a confirmation never
creates a second order. Quotes expire after ten minutes.

The agent remembers request details across clarification turns in the same conversation
for up to 24 hours (bounded history). Say `start` to clear request memory. Fractional
hour deadlines are supported. Infeasible requests return concrete alternatives without
silently changing your constraints.

Tracking reports persisted operator-entered demo milestones: reserved → packing →
dispatched → delivered. It is not courier GPS and does not advance automatically.
The operations dashboard refreshes the tracking panel every five seconds. ASI:One users
can request updates with `track ORDER-ID`. Automatic cancellation is blocked once any
shipment has been dispatched; contact the operator then.

## Demo boundaries

All suppliers and inventory are explicitly labelled demo data. Reservations change a
persistent database, but do not buy real products, dispatch a delivery, or collect money.
Notebooks, pens, lanyards, markers, folders, and badges are supported. Pickup/fulfilment estimates are supplier
fixtures, not live traffic predictions. Payment Protocol is not implemented. The current
network uses a shared transactional inventory store, not independently operated merchants.
No external website is required to complete the ASI:One workflow.
