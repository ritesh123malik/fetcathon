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
- "cancel SR-XXXXXXXX" releases a reservation you own.

## What happens

The coordinator requests stock snapshots from three supplier uAgents. A deterministic
planner checks quantities, cost, deadline and stock. You review a plan before confirming.
Confirmation revalidates every item and atomically reserves stock. If a supplier changes
availability, a revised quote requires your approval. Retrying a confirmation never
creates a second order. Quotes expire after ten minutes.

## Demo boundaries

All suppliers and inventory are explicitly labelled demo data. Reservations change a
persistent database, but do not buy real products, dispatch a delivery, or collect money.
Only notebooks, pens, and lanyards are supported. Pickup/fulfilment estimates are supplier
fixtures, not live traffic predictions. Payment Protocol is not implemented. The current
network uses a shared transactional inventory store, not independently operated merchants.
No external website is required to complete the ASI:One workflow.
