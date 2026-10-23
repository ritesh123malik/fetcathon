# Fetch-A-Thon submission packet

## Project description

**SupplyRescue — your backup plan, handled.**

Campus organisers lose time calling replacement suppliers when stationery orders fall
through. SupplyRescue accepts a goal, gathers stock from specialised supplier agents,
computes a complete allocation within budget and deadline, and asks the user to approve.
It then atomically reserves inventory and returns a receipt. If a supplier becomes
unavailable, it replans and asks for new approval instead of creating a partial order.

Target users: campus event organisers and small operations teams.

Outcome: a persistent, confirmed demo-inventory order with reservation references,
plus auditable recovery and cancellation. This is not a real merchant purchase.

## Requirements checklist

| Requirement | Implementation / evidence |
| --- | --- |
| Registered Agentverse agent | Coordinator profile linked in root README |
| Agent Chat Protocol | Official `chat_protocol_spec`, acknowledgements, native messages |
| ASI:One core reasoning | Live API intent extraction with schema validation |
| Meaningful execution | Atomic inventory reservation, release and receipts |
| Multi-agent collaboration | Coordinator requests snapshots from three distinct uAgents |
| Complete workflow inside ASI:One | Form → carousel → review → receipt; status and cancellation |
| Interactive Cards | Native form, carousel and review metadata payloads |
| Reliability | Expiry, stale-stock recovery, duplicate prevention, ownership tests |
| Public code | https://github.com/ritesh123malik/fetcathon |
| Payment Protocol | Not implemented; do not claim this optional bonus |

## Still required before final submission

- Verify the deployed worker stays online on Render.
- Verify discovery and every card round trip in the real ASI:One UI.
- Create and submit the **public ASI:One Shared Chat URL**.
- Record and submit the **3–5 minute demo video**.
- Submit the repository, Agentverse profile, shared chat and video through Devpost.

Do not mark these complete just because the code supports them. Do not share the build
conversation containing credentials; record a separate clean product demonstration.

## Four-minute demo script

**0:00–0:25 — Problem.** “The workshop starts tomorrow. Our stationery supplier has
cancelled. We need 60 notebooks and 60 pens under INR 4,500.”

**0:25–1:10 — Intent and collaboration.** Send the request in ASI:One. Explain that the
coordinator asks three supplier agents for inventory and uses deterministic constraints
to compute plans. Show the native option carousel.

**1:10–1:45 — Review.** Select the best-value plan. Show quantities, supplier split,
fulfilment estimate and price in the review card. Nothing has been reserved yet.

**1:45–2:35 — Recovery.** An operator pauses the cheapest supplier. Confirm the original
offer in ASI:One. Show the replacement plan and explain that no partial order was placed.
Approve the new plan.

**2:35–3:15 — Evidence.** Show the receipt and reservation IDs in ASI:One. Ask for `orders`.
Briefly show the operations inventory and execution trail as secondary evidence.

**3:15–3:45 — Release and reliability.** Cancel the order in the same conversation.
Explain that retries cannot duplicate fulfilment or restore stock twice.

**3:45–4:00 — Scope and next step.** “These are labelled demo suppliers with real database
transactions. A campus supplier pilot is the next step. The primary flow needs no custom
frontend.”

## Positioning

Lead with successful commitments and recovery, not the number of frameworks. Distinguish
LLM intent extraction from deterministic arithmetic. Do not claim live merchant stock,
real deliveries, payment settlement, or horizontal scalability.
