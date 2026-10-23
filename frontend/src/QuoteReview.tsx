import { useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  Clock3,
  Download,
  LoaderCircle,
  ShieldCheck,
  Users,
} from "lucide-react";
import { api, money, time } from "./api";
import { Modal, Notice, Status } from "./components";
import type { ConfirmResult, Order, Quote } from "./types";

export function Receipt({ order }: { order: Order }) {
  const download = () => {
    const blob = new Blob([JSON.stringify(order, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${order.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div className="receipt">
      <div className="receipt-check">
        <CheckCircle2 size={34} />
      </div>
      <span className="eyebrow">
        {order.status === "cancelled"
          ? "INVENTORY RELEASED"
          : "INVENTORY COMMITTED"}
      </span>
      <h2>
        {order.status === "cancelled"
          ? "This reservation was cancelled."
          : "Your backup plan is in place."}
      </h2>
      <p>
        {order.payload.title} · {order.payload.location}
      </p>
      <div className="receipt-number">
        <span>Order reference</span>
        <strong>{order.id}</strong>
      </div>
      <div className="receipt-lines">
        {order.payload.lines.map((l, i) => (
          <div key={i}>
            <span>
              {l.quantity} × {l.product}s <small>{l.supplier_name}</small>
            </span>
            <strong>{money(l.quantity * l.unit_paise)}</strong>
          </div>
        ))}
        <div className="receipt-total">
          <span>Total</span>
          <strong>{money(order.payload.total_paise)}</strong>
        </div>
      </div>
      <div className="reservation-list">
        {order.payload.reservations.map((r) => (
          <span key={r.id}>
            <ShieldCheck size={14} />
            {r.id}
          </span>
        ))}
      </div>
      <p className="muted">
        Supplier fulfilment estimate: {order.payload.eta_hours} hours.
        <br />
        Reservation receipt; no payment has been collected.
      </p>
      <button className="button secondary" onClick={download}>
        <Download size={16} /> Download receipt
      </button>
    </div>
  );
}

export default function QuoteReview({
  initial,
  onClose,
  onChange,
}: {
  initial: Quote;
  onClose: () => void;
  onChange: () => void;
}) {
  const [quote, setQuote] = useState(initial);
  const [selected, setSelected] = useState(initial.options[0]?.id || "");
  const [order, setOrder] = useState<Order | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [recovery, setRecovery] = useState("");
  async function confirm() {
    setBusy(true);
    setError("");
    try {
      const result = await api<ConfirmResult>(
        `/quotes/${quote.id}/confirm`,
        "POST",
        { option_id: selected },
      );
      if (result.status === "confirmed") setOrder(result.order);
      else {
        setQuote(result.quote);
        setSelected(result.quote.options[0]?.id || "");
        setRecovery(result.reason + " Please review the updated plan.");
      }
      onChange();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal
      title={
        order
          ? "Rescue confirmed"
          : quote.options.length
            ? "Your rescue options"
            : "Let’s adjust the request"
      }
      onClose={onClose}
      wide
    >
      {order ? (
        <div className="modal-body">
          <Receipt order={order} />
        </div>
      ) : (
        <div className="modal-body">
          <div className="quote-meta">
            <span>{quote.id}</span>
            <Status status={quote.status} />
            <span>
              <Clock3 size={14} />
              Quote valid until {time(quote.expires_at)}
            </span>
          </div>
          <h3 className="quote-title">{quote.requirements.title}</h3>
          <p className="muted">
            {quote.requirements.items
              .map((i) => `${i.quantity} ${i.product}s`)
              .join(" + ")}{" "}
            · Budget {money(quote.requirements.budget_paise)} · Within{" "}
            {quote.requirements.deadline_hours}h
          </p>
          {recovery && <Notice>{recovery}</Notice>}
          <div className="option-grid">
            {quote.options.map((option) => (
              <button
                key={option.id}
                className={`option ${selected === option.id ? "chosen" : ""}`}
                onClick={() => setSelected(option.id)}
                aria-pressed={selected === option.id}
              >
                <div className="option-heading">
                  <span>{option.label}</span>
                  <span className="radio-dot" />
                </div>
                <strong className="option-price">
                  {money(option.total_paise)}
                </strong>
                <small>
                  {money(quote.requirements.budget_paise - option.total_paise)}{" "}
                  within budget
                </small>
                <div className="option-facts">
                  <span>
                    <Clock3 size={14} />
                    {option.eta_hours}h fulfilment
                  </span>
                  <span>
                    <Users size={14} />
                    {option.supplier_count} supplier
                    {option.supplier_count > 1 ? "s" : ""}
                  </span>
                </div>
                <div className="option-lines">
                  {option.lines.map((line, i) => (
                    <div key={i}>
                      <span>
                        {line.quantity} {line.product}s
                      </span>
                      <small>{line.supplier_name}</small>
                    </div>
                  ))}
                </div>
              </button>
            ))}
          </div>
          {!quote.options.length && (
            <Notice>
              No complete plan fits your current stock, deadline, and budget.
              Close this panel and try a new request with a higher budget, more
              time, or fewer items.
            </Notice>
          )}
          <div className="timeline">
            <h4>
              Execution trail <span>Recorded by the sourcing engine</span>
            </h4>
            {quote.events.map((event) => (
              <div className="timeline-item" key={event.id}>
                <span
                  className={`timeline-dot ${event.kind === "recovery" ? "warning" : ""}`}
                />
                <div>
                  <p>{event.message}</p>
                  <small>{time(event.created_at)}</small>
                </div>
              </div>
            ))}
          </div>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          <div className="review-footer">
            <p>
              <ShieldCheck size={16} />
              Stock rechecked before confirmation.
              <br />
              Nothing is committed if any supplier fails.
            </p>
            <button
              className="button primary"
              disabled={busy || !selected || quote.status !== "quoted"}
              onClick={confirm}
            >
              {busy ? (
                <LoaderCircle className="spin" size={17} />
              ) : (
                <ArrowRight size={17} />
              )}{" "}
              Confirm selected plan
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}
