import {
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  Package,
  Truck,
} from "lucide-react";
import type { Dashboard } from "./types";
import { PRODUCTS, PRODUCT_LABELS } from "./types";

export default function OperationsOverview({
  data,
  onSuppliers,
  onOrders,
  onTrack,
}: {
  data: Dashboard;
  onSuppliers: () => void;
  onOrders: () => void;
  onTrack: (id: string) => void;
}) {
  const low = data.suppliers.flatMap((s) =>
    s.inventory
      .filter((i) => i.stock < 20)
      .map((i) => ({ ...i, name: s.name })),
  );
  const overdue = data.orders.filter((o) =>
    o.shipments?.some((s) => s.overdue),
  );
  const stages = ["reserved", "packing", "dispatched", "delivered"];
  const shipments = data.orders.flatMap((o) => o.shipments || []);
  const maxStock = Math.max(
    1,
    ...PRODUCTS.map((p) =>
      data.suppliers
        .filter((s) => s.active)
        .reduce(
          (n, s) => n + (s.inventory.find((i) => i.product === p)?.stock || 0),
          0,
        ),
    ),
  );
  return (
    <div className="ops-grid">
      <section className="panel ops-panel">
        <div className="ops-heading">
          <div>
            <span className="eyebrow">FULFILMENT PULSE</span>
            <h2>Every commitment, moving.</h2>
          </div>
          <button
            className="icon-button"
            aria-label="View orders"
            onClick={onOrders}
          >
            <ArrowUpRight size={20} />
          </button>
        </div>
        <div className="pipeline">
          {stages.map((stage, i) => (
            <button
              key={stage}
              onClick={onOrders}
              className={`pipeline-stage stage-${i}`}
            >
              <span>
                {i === 3 ? (
                  <CheckCircle2 size={18} />
                ) : i === 2 ? (
                  <Truck size={18} />
                ) : (
                  <Package size={18} />
                )}
              </span>
              <strong>
                {shipments.filter((s) => s.status === stage).length}
              </strong>
              <small>{stage}</small>
            </button>
          ))}
        </div>
        <p className="ops-note">
          Supplier shipments · Operator-reported demo progress
        </p>
      </section>
      <section className="panel ops-panel">
        <div className="ops-heading">
          <div>
            <span className="eyebrow">AVAILABLE TO SOURCE</span>
            <h2>Inventory coverage</h2>
          </div>
          <button
            className="icon-button"
            aria-label="Manage inventory"
            onClick={onSuppliers}
          >
            <ArrowUpRight size={20} />
          </button>
        </div>
        <div className="stock-bars">
          {PRODUCTS.map((p) => {
            const units = data.suppliers
              .filter((s) => s.active)
              .reduce(
                (n, s) =>
                  n + (s.inventory.find((i) => i.product === p)?.stock || 0),
                0,
              );
            return (
              <div key={p}>
                <span>{PRODUCT_LABELS[p]}</span>
                <div className="stock-bar">
                  <i style={{ width: `${(100 * units) / maxStock}%` }} />
                </div>
                <strong>{units}</strong>
              </div>
            );
          })}
        </div>
        <p className="ops-note">
          Available units across suppliers accepting orders
        </p>
      </section>
      <section className="panel ops-panel attention-panel">
        <div className="ops-heading">
          <div>
            <span className="eyebrow">ATTENTION QUEUE</span>
            <h2>
              {low.length + overdue.length
                ? `${low.length + overdue.length} things to check`
                : "All clear for now"}
            </h2>
          </div>
          <AlertTriangle size={22} />
        </div>
        {!low.length && !overdue.length && (
          <p className="ops-note">
            No inventory below 20 units or overdue shipments.
          </p>
        )}
        {overdue.slice(0, 3).map((o) => (
          <button
            className="attention-row"
            key={o.id}
            onClick={() => onTrack(o.id)}
          >
            <Truck size={17} />
            <span>
              <strong>Delivery estimate overdue</strong>
              <small>{o.id} · Ask the operator for an update</small>
            </span>
            <ArrowUpRight size={16} />
          </button>
        ))}
        {low.slice(0, 4).map((i) => (
          <button
            className="attention-row"
            key={i.name + i.product}
            onClick={onSuppliers}
          >
            <Package size={17} />
            <span>
              <strong>
                {i.stock === 0 ? "Out of stock" : "Low stock"} ·{" "}
                {PRODUCT_LABELS[i.product]}
              </strong>
              <small>
                {i.name} · {i.stock} units remaining
              </small>
            </span>
            <ArrowUpRight size={16} />
          </button>
        ))}
        {low.length > 4 && (
          <button className="text-button" onClick={onSuppliers}>
            View all inventory alerts →
          </button>
        )}
      </section>
    </div>
  );
}
