import { useEffect, useState } from "react";
import { api } from "./api";
import { Modal, Notice } from "./components";

interface Shipment {
  supplier_id: string;
  supplier_name: string;
  reservation_id: string;
  status: string;
  estimated_delivery: string;
  overdue: boolean;
  history: { status: string; note: string; created_at: string }[];
}
interface Tracking {
  order_id: string;
  location: string;
  status: string;
  shipments: Shipment[];
  updated_at: string;
}
const stages = ["reserved", "packing", "dispatched", "delivered"];
export default function OrderTracking({
  orderId,
  demo,
  onClose,
}: {
  orderId: string;
  demo: boolean;
  onClose: () => void;
}) {
  const [report, setReport] = useState<Tracking | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");
  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await api<Tracking>(`/orders/${orderId}/tracking`);
        if (active) {
          setReport(data);
          setError("");
        }
      } catch (e) {
        if (active) setError((e as Error).message);
      }
    };
    void load();
    const timer = window.setInterval(load, 5000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [orderId]);
  async function advance(shipment: Shipment) {
    setBusy(true);
    try {
      setReport(
        await api<Tracking>(
          `/orders/${orderId}/shipments/${shipment.supplier_id}`,
          "POST",
          { status: stages[stages.indexOf(shipment.status) + 1], note },
        ),
      );
      setNote("");
      setError("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal title={`Track order ${orderId}`} onClose={onClose}>
      <div className="modal-body">
        <Notice>
          Demo fulfilment updates reported by the operator. Refreshes every 5
          seconds. No courier integration or GPS tracking.
        </Notice>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {!report && !error && <p role="status">Loading shipments…</p>}
        {report && (
          <>
            <p>
              <strong>{report.location}</strong> ·{" "}
              {report.status.replaceAll("_", " ")}
            </p>
            <small>
              Last refreshed: {new Date(report.updated_at).toLocaleTimeString()}
            </small>
            {report.shipments.map((s) => (
              <section className="panel tracking-shipment" key={s.supplier_id}>
                <h3>{s.supplier_name}</h3>
                <small>{s.reservation_id}</small>
                <p>
                  <strong>{s.status.toUpperCase()}</strong> · Estimated arrival{" "}
                  {new Date(s.estimated_delivery).toLocaleString()}
                </p>
                {s.overdue && (
                  <Notice>
                    Estimate overdue. Ask the operator for an update; delivery
                    is not assumed.
                  </Notice>
                )}
                <ol
                  className="tracking-stages"
                  aria-label="Fulfilment progress"
                >
                  {stages.map((stage, i) => (
                    <li
                      key={stage}
                      className={
                        s.status !== "cancelled" &&
                        stages.indexOf(s.status) >= i
                          ? "complete"
                          : ""
                      }
                    >
                      {stage}
                    </li>
                  ))}
                </ol>
                <div className="timeline">
                  {s.history.map((h, i) => (
                    <div className="timeline-item" key={i}>
                      <span className="timeline-dot" />
                      <div>
                        <p>
                          {h.status} — {h.note}
                        </p>
                        <small>{new Date(h.created_at).toLocaleString()}</small>
                      </div>
                    </div>
                  ))}
                </div>
                {demo &&
                  stages.includes(s.status) &&
                  s.status !== "delivered" && (
                    <button
                      className="button secondary small"
                      disabled={busy}
                      onClick={() => void advance(s)}
                    >
                      Demo: mark {stages[stages.indexOf(s.status) + 1]}
                    </button>
                  )}
              </section>
            ))}
            {demo && (
              <label className="field">
                Optional note for next demo update
                <input
                  maxLength={300}
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="e.g. Packed and checked by campus operator"
                />
              </label>
            )}
          </>
        )}
      </div>
    </Modal>
  );
}
