# Deployment

## Laptop + Mailbox demo (no cloud hosting fee)

This is the selected hackathon setup. Code and SQLite data stay on your laptop;
the registered coordinator retrieves messages from Agentverse Mailbox. No Render
service or public inbound tunnel is required. ASI:One usage and Agentverse plan
limits still apply.

From the repository root, using the existing private `.env`:

```bash
make build
# macOS: prevent idle sleep while the demo runs
caffeinate -i make demo
# Other platforms: make demo (disable idle sleep yourself)
```

Open http://127.0.0.1:8000 for operations. The dashboard binds to loopback only.
Use the Agentverse profile linked in the README to open the primary ASI:One flow.
Keep the terminal running, the Mac plugged in, the lid open and internet connected.
`caffeinate` prevents idle sleep; it does not guarantee operation with the lid closed.
Ctrl+C stops the server and agents. Run the same command to restart; existing orders
and inventory remain in `data/supplyrescue.sqlite3`. Do not delete the data directory
or change `AGENT_SEED` between runs. Do not run another worker with the same seed.

Before judging, run `uv run python -m scripts.check_connections`, verify a complete
request/review/confirm/status/cancel flow in ASI:One, then create its public shared
chat and record the required video. Local tests do not establish ASI:One UI support.
This setup is available only while the laptop worker is running, not 24/7 hosting.

## Local preview

Build the frontend, then run `uv run python -m scripts.serve`. It serves the React build
and API together. Set `RUN_AGENTS=true` to also supervise the agent worker. If either
child process exits unexpectedly, the supervisor terminates the other and exits so a
hosting platform can restart the service.

## Render blueprint

The repository includes `render.yaml` and a multi-stage Dockerfile. It defines one
**Starter web service with a 1 GB persistent disk** in Singapore. This is a paid hosting
configuration; review the current Render price before creating it. No service purchase
is implied by merely committing the blueprint.

1. In Render, choose **New → Blueprint** and connect
   `https://github.com/ritesh123malik/fetcathon`.
2. Review the service and disk charges before approving creation.
3. Set the secret environment variables in Render:

   | Variable | Purpose |
   | --- | --- |
   | `ASI_ONE_API_KEY` | ASI:One intent extraction |
   | `AGENTVERSE_API_KEY` | Registration and platform API access |
   | `AGENT_SEED` | Same private identity seed used by the registered coordinator |
   | `AGENT_PROFILE_URL` | Registered Agentverse profile link |

   Render generates `ADMIN_API_KEY`. Retrieve it privately from the dashboard to sign
   into the operations UI. Do not place this key into frontend environment variables.

4. Keep `DATABASE_PATH=/app/data/supplyrescue.sqlite3`, `RUN_AGENTS=true`, and
   `AGENT_MAILBOX=true`. Demo suppliers remain clearly labelled with `DEMO_MODE=true`.
5. Deploy. Confirm `/api/health` returns `{"status":"ok"}` and inspect worker logs for
   successful mailbox connectivity. A healthy HTTP server alone does not prove ACP delivery.
6. Stop the local worker before starting the deployed worker with the same agent seed.
   Two workers sharing one identity but different databases would produce inconsistent state.
7. Open the deployed UI, enter the operator key, and test inventory and an order.
8. Test the same complete workflow through ASI:One, including review, confirmation,
   status, and cancellation. Create the public shared chat only after this succeeds.

The service uses a single disk and one instance. Do not enable horizontal scaling without
migrating the database. Back up the disk before schema changes. No persistent disk means
orders may disappear on redeploy; do not use that configuration for judging.

## Agent registration

`uv run python -m scripts.register_agent` proves ownership using the private seed,
publishes the agent's README/ACP capabilities and records the profile URL in `.env`.
For a new deployment use the same seed to preserve the existing address. Use a new seed
only when intentionally creating a different identity.

Mailbox mode queues incoming messages; the Python process must still be running to
receive and handle them. No wallet funding is required by the application. uAgents may
log an informational insufficient-funds warning for on-chain registration; the application
does not fund wallets or initiate blockchain transactions.

## Docker locally

```bash
docker build -t supplyrescue .
docker run --rm -p 8000:8000 --env-file .env \
  -e ADMIN_API_KEY='<private-operator-key>' \
  -e RUN_AGENTS=true -v supplyrescue-data:/app/data supplyrescue
```

Supply secrets using a trusted shell/secret manager. Do not copy this command with real
credentials into a public README, chat, screenshot or recording.

## Verification status

The release notes in `docs/SUBMISSION.md` distinguish implemented features from external
checks still required. Never label registration, a successful build, or a health check
as proof of the complete ASI:One workflow.
