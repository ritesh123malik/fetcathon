import { useState } from "react";
import { ArrowRight, LoaderCircle, Plus, Sparkles, Trash2 } from "lucide-react";
import { api } from "./api";
import { Modal, Notice } from "./components";
import type { Config, Product, Quote, Requirements } from "./types";

export default function RequestForm({
  onClose,
  onCreated,
  config,
}: {
  onClose: () => void;
  onCreated: (q: Quote) => void;
  config: Config | null;
}) {
  const [requirements, setRequirements] = useState<Requirements>({
    title: "Workshop supplies",
    location: "Bengaluru campus",
    budget_paise: 450000,
    deadline_hours: 24,
    items: [
      { product: "notebook", quantity: 60 },
      { product: "pen", quantity: 60 },
    ],
  });
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [parsed, setParsed] = useState(false);
  async function interpret() {
    setBusy("interpret");
    setError("");
    try {
      const data = await api<{ requirements: Requirements }>(
        "/intent",
        "POST",
        { message: prompt },
      );
      setRequirements(data.requirements);
      setParsed(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy("quote");
    setError("");
    try {
      onCreated(await api<Quote>("/quotes", "POST", { requirements }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  return (
    <Modal title="Let's rescue your supply run." onClose={onClose}>
      <div className="modal-body">
        <p className="muted form-intro">
          Tell us what you need. We’ll find a complete plan that fits your
          budget and deadline.
        </p>
        <div className="intent-box">
          <label htmlFor="intent">
            <Sparkles size={16} />
            {config?.ai_connected
              ? "Describe it with ASI:One"
              : "Try a quick request"}
          </label>
          <textarea
            id="intent"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="60 notebooks and 60 pens under ₹4,500 within 24 hours"
            rows={2}
          />
          <div className="intent-footer">
            <small>
              {config?.ai_connected
                ? "Powered by ASI:One"
                : "Offline demo parser · quantities, budget & hours"}
            </small>
            <button
              type="button"
              disabled={!prompt.trim() || !!busy}
              className="button small secondary"
              onClick={interpret}
            >
              {busy === "interpret" ? (
                <LoaderCircle className="spin" size={15} />
              ) : (
                <Sparkles size={15} />
              )}{" "}
              Fill details
            </button>
          </div>
        </div>
        {parsed && (
          <Notice success>
            Request understood. Review the details below before sourcing.
          </Notice>
        )}
        <form onSubmit={submit}>
          <label className="field">
            Request name
            <input
              required
              maxLength={100}
              value={requirements.title}
              onChange={(e) =>
                setRequirements({ ...requirements, title: e.target.value })
              }
            />
          </label>
          <div className="field-label">
            What do you need?<span>Available catalogue</span>
          </div>
          <div className="items-form">
            {requirements.items.map((item, index) => (
              <div className="item-input" key={index}>
                <select
                  aria-label={`Product ${index + 1}`}
                  value={item.product}
                  onChange={(e) =>
                    setRequirements({
                      ...requirements,
                      items: requirements.items.map((v, i) =>
                        i === index
                          ? { ...v, product: e.target.value as Product }
                          : v,
                      ),
                    })
                  }
                >
                  {(["notebook", "pen", "lanyard"] as Product[])
                    .filter(
                      (p) =>
                        p === item.product ||
                        !requirements.items.some((i) => i.product === p),
                    )
                    .map((p) => (
                      <option key={p} value={p}>
                        {p === "notebook"
                          ? "A5 notebooks"
                          : p === "pen"
                            ? "Ballpoint pens"
                            : "Event lanyards"}
                      </option>
                    ))}
                </select>
                <div className="quantity">
                  <input
                    aria-label={`Quantity ${index + 1}`}
                    required
                    type="number"
                    min="1"
                    max="1000"
                    value={item.quantity}
                    onChange={(e) =>
                      setRequirements({
                        ...requirements,
                        items: requirements.items.map((v, i) =>
                          i === index
                            ? { ...v, quantity: Number(e.target.value) }
                            : v,
                        ),
                      })
                    }
                  />
                  <span>units</span>
                </div>
                <button
                  type="button"
                  className="icon-button"
                  disabled={requirements.items.length === 1}
                  aria-label={`Remove product ${index + 1}`}
                  onClick={() =>
                    setRequirements({
                      ...requirements,
                      items: requirements.items.filter((_, i) => i !== index),
                    })
                  }
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
          {requirements.items.length < 3 && (
            <button
              className="text-button"
              type="button"
              onClick={() =>
                setRequirements({
                  ...requirements,
                  items: [
                    ...requirements.items,
                    {
                      product: (
                        ["notebook", "pen", "lanyard"] as Product[]
                      ).find(
                        (p) => !requirements.items.some((i) => i.product === p),
                      )!,
                      quantity: 30,
                    },
                  ],
                })
              }
            >
              <Plus size={15} /> Add another item
            </button>
          )}
          <div className="form-grid">
            <label className="field">
              Maximum budget (₹)
              <input
                required
                type="number"
                min="1"
                max="100000"
                value={requirements.budget_paise / 100}
                onChange={(e) =>
                  setRequirements({
                    ...requirements,
                    budget_paise: Math.round(Number(e.target.value) * 100),
                  })
                }
              />
            </label>
            <label className="field">
              Needed within (hours)
              <input
                required
                type="number"
                min="1"
                max="168"
                value={requirements.deadline_hours}
                onChange={(e) =>
                  setRequirements({
                    ...requirements,
                    deadline_hours: Number(e.target.value),
                  })
                }
              />
            </label>
          </div>
          <label className="field">
            Fulfilment location
            <input
              required
              minLength={2}
              maxLength={120}
              value={requirements.location}
              onChange={(e) =>
                setRequirements({ ...requirements, location: e.target.value })
              }
            />
          </label>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <div className="form-bottom">
            <p>
              No orders placed until you approve.
              <br />
              {config?.demo_mode
                ? "Demo suppliers · real inventory transactions"
                : "Inventory is rechecked at confirmation."}
            </p>
            <button className="button primary" disabled={!!busy}>
              {busy === "quote" ? (
                <LoaderCircle size={17} className="spin" />
              ) : (
                <ArrowRight size={17} />
              )}{" "}
              Find my rescue plan
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
}
