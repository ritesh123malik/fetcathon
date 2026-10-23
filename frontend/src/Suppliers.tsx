import { PRODUCT_LABELS } from "./types";
import { useState } from "react";
import { Clock3, MapPin, Save } from "lucide-react";
import { api, money } from "./api";
import type { Supplier } from "./types";

export default function Suppliers({
  suppliers,
  onChange,
}: {
  suppliers: Supplier[];
  onChange: () => void;
}) {
  const [editing, setEditing] = useState<string | null>(null);
  const [stock, setStock] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function toggle(s: Supplier) {
    setBusy(true);
    setError("");
    try {
      await api(`/suppliers/${s.id}/availability`, "PATCH", {
        active: !s.active,
      });
      onChange();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function save(supplier: string, product: string) {
    setBusy(true);
    setError("");
    try {
      await api(`/suppliers/${supplier}/inventory/${product}`, "PATCH", {
        stock,
      });
      setEditing(null);
      onChange();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="supplier-grid">
        {suppliers.map((s) => (
          <article key={s.id} className="supplier-card">
            <header>
              <span className={`supplier-avatar ${s.color}`}>{s.initials}</span>
              <div>
                <h3>{s.name}</h3>
                <p>
                  <MapPin size={12} />
                  {s.area}
                </p>
              </div>
            </header>
            <div className="supplier-info">
              <span>
                <Clock3 size={14} />
                {s.eta_hours}h fulfilment
              </span>
              <span className={`network-status ${s.active ? "" : "paused"}`}>
                <i />
                {s.active ? "Available" : "Paused"}
              </span>
            </div>
            <div className="inventory-table">
              <div className="inventory-heading">
                <span>PRODUCT</span>
                <span>PRICE</span>
                <span>AVAILABLE</span>
              </div>
              {s.inventory.map((item) => (
                <div className="inventory-row" key={item.product}>
                  <strong>{PRODUCT_LABELS[item.product]}</strong>
                  <span>{money(item.unit_paise)}</span>
                  {editing === `${s.id}-${item.product}` ? (
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        void save(s.id, item.product);
                      }}
                    >
                      <input
                        autoFocus
                        aria-label={`${s.name} ${item.product} stock`}
                        type="number"
                        required
                        min="0"
                        max="10000"
                        value={stock}
                        onChange={(e) => setStock(Number(e.target.value))}
                      />
                      <button
                        className="icon-button"
                        disabled={busy}
                        aria-label="Save stock"
                      >
                        <Save size={14} />
                      </button>
                    </form>
                  ) : (
                    <button
                      title="Edit available stock"
                      onClick={() => {
                        setEditing(`${s.id}-${item.product}`);
                        setStock(item.stock);
                      }}
                    >
                      {item.stock}
                      <span> units</span>
                    </button>
                  )}
                </div>
              ))}
            </div>
            <button
              disabled={busy}
              className={`button full ${s.active ? "secondary" : "primary"}`}
              onClick={() => toggle(s)}
            >
              {s.active ? "Pause new orders" : "Resume new orders"}
            </button>
          </article>
        ))}
      </div>
      <div className="explanation">
        <strong>Test the recovery flow</strong>
        <p>
          Create a rescue request, then pause a supplier included in its offer.
          Return to the request and confirm: SupplyRescue will replan without
          committing partial inventory. Review and approve the replacement
          offer.
        </p>
      </div>
    </>
  );
}
