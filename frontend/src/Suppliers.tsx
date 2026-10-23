import { PRODUCT_LABELS } from "./types";
import { useState } from "react";
import { Clock3, MapPin, Save, Search, X } from "lucide-react";
import { api, money } from "./api";
import type { Supplier } from "./types";

export default function Suppliers({
  suppliers,
  onChange,
}: {
  suppliers: Supplier[];
  onChange: () => void;
}) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const visible = suppliers.filter(
    (s) =>
      `${s.name} ${s.area} ${s.inventory.map((i) => i.product).join(" ")}`
        .toLowerCase()
        .includes(query.toLowerCase()) &&
      (filter === "all" ||
        (filter === "active" && s.active) ||
        (filter === "paused" && !s.active) ||
        (filter === "low" && s.inventory.some((i) => i.stock < 20))),
  );
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
      <div className="workspace-toolbar">
        <label className="search">
          <Search size={16} />
          <input
            aria-label="Search suppliers"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search supplier, area or product…"
          />
        </label>
        <span className="muted">
          {visible.length} of {suppliers.length} suppliers
        </span>
      </div>
      <div className="filter-tabs">
        {[
          ["all", "All suppliers"],
          ["active", "Accepting orders"],
          ["paused", "Paused"],
          ["low", "Low / out of stock"],
        ].map(([value, label]) => (
          <button
            key={value}
            className={filter === value ? "selected" : ""}
            aria-pressed={filter === value}
            onClick={() => setFilter(value)}
          >
            {label}
          </button>
        ))}
      </div>
      {!visible.length && (
        <div className="panel ops-panel">
          No suppliers match.{" "}
          <button
            className="text-button"
            onClick={() => {
              setQuery("");
              setFilter("all");
            }}
          >
            Clear filters
          </button>
        </div>
      )}
      <div className="supplier-grid">
        {visible.map((s) => (
          <article
            key={s.id}
            className={`supplier-card ${s.active ? "" : "supplier-paused"}`}
          >
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
                <div
                  className={`inventory-row ${item.stock === 0 ? "stock-empty" : item.stock < 20 ? "stock-low" : ""}`}
                  key={item.product}
                >
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
                      <button
                        type="button"
                        className="icon-button"
                        aria-label="Cancel stock edit"
                        disabled={busy}
                        onClick={() => setEditing(null)}
                      >
                        <X size={14} />
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
                      {item.stock === 0 ? "Out of stock" : item.stock}
                      {item.stock > 0 && (
                        <span> units{item.stock < 20 ? " · Low" : ""}</span>
                      )}
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
