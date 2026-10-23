import { useState } from "react";
import { Download, Search, Truck, ArrowUpRight } from "lucide-react";
import { money } from "./api";
import { Empty } from "./components";
import type { Order } from "./types";

export default function Orders({
  orders,
  onTrack,
  onReceipt,
  onCancel,
  onNew,
}: {
  orders: Order[];
  onTrack: (id: string) => void;
  onReceipt: (o: Order) => void;
  onCancel: (o: Order) => void;
  onNew: () => void;
}) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [sort, setSort] = useState("newest");
  const filtered = orders
    .filter(
      (o) =>
        `${o.id} ${o.payload.title} ${o.payload.location} ${o.payload.lines.map((l) => l.supplier_name + " " + l.product).join(" ")}`
          .toLowerCase()
          .includes(search.toLowerCase()) &&
        (filter === "all" ||
          (filter === "overdue" && o.shipments?.some((s) => s.overdue)) ||
          (o.fulfilment_status || o.status) === filter),
    )
    .sort((a, b) =>
      sort === "value"
        ? b.payload.total_paise - a.payload.total_paise
        : sort === "oldest"
          ? a.created_at.localeCompare(b.created_at)
          : b.created_at.localeCompare(a.created_at),
    );
  function download() {
    const blob = new Blob([JSON.stringify(filtered, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "supplyrescue-orders.json";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <>
      <div className="workspace-toolbar">
        <label className="search">
          <Search size={16} />
          <input
            aria-label="Search orders"
            placeholder="Order, supplier, product or location…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <select
          aria-label="Sort orders"
          value={sort}
          onChange={(e) => setSort(e.target.value)}
        >
          <option value="newest">Newest first</option>
          <option value="oldest">Oldest first</option>
          <option value="value">Highest value</option>
        </select>
        <button
          className="button secondary small"
          disabled={!filtered.length}
          onClick={download}
        >
          <Download size={15} /> Export results
        </button>
      </div>
      <div className="filter-tabs" aria-label="Filter orders">
        {[
          ["all", "All orders"],
          ["in_progress", "In progress"],
          ["delivered", "Delivered"],
          ["cancelled", "Cancelled"],
          ["overdue", "Overdue"],
        ].map(([key, label]) => (
          <button
            key={key}
            aria-pressed={filter === key}
            onClick={() => setFilter(key)}
            className={filter === key ? "selected" : ""}
          >
            {label}
          </button>
        ))}
        <span>{filtered.length} results</span>
      </div>
      <div className="orders-list">
        {filtered.map((o) => (
          <section className="panel order-card enhanced-order" key={o.id}>
            <div className="order-heading">
              <span className="request-icon">
                <Truck size={23} />
              </span>
              <div>
                <small>
                  {o.id} · {new Date(o.created_at).toLocaleDateString("en-IN")}
                </small>
                <h3>{o.payload.title}</h3>
              </div>
              <span className={`fulfilment-pill ${o.fulfilment_status}`}>
                {(o.fulfilment_status || o.status).replaceAll("_", " ")}
              </span>
            </div>
            <div className="order-details">
              <div>
                <span>Reserved value</span>
                <strong>{money(o.payload.total_paise)}</strong>
              </div>
              <div>
                <span>Destination</span>
                <strong>{o.payload.location}</strong>
              </div>
              <div>
                <span>Basket</span>
                <strong>
                  {o.payload.lines.reduce((n, l) => n + l.quantity, 0)} units ·{" "}
                  {o.payload.supplier_count} suppliers
                </strong>
              </div>
            </div>
            <div className="shipment-strip">
              {o.shipments?.map((s) => (
                <button
                  key={s.supplier_id}
                  onClick={() => onTrack(o.id)}
                  className={s.overdue ? "is-overdue" : ""}
                >
                  <span>
                    <strong>{s.supplier_name}</strong>
                    <small>
                      {s.overdue
                        ? "Estimate overdue"
                        : s.status === "cancelled"
                          ? "Inventory released"
                          : s.status === "delivered"
                            ? "Delivery reported"
                            : `Estimate: ${new Date(s.estimated_delivery).toLocaleString("en-IN")}`}
                    </small>
                  </span>
                  <span>
                    {s.status} <ArrowUpRight size={13} />
                  </span>
                </button>
              ))}
            </div>
            <div className="order-footer">
              <button
                className="button primary small"
                onClick={() => onTrack(o.id)}
              >
                <Truck size={14} /> Track shipments
              </button>
              <button
                className="button secondary small"
                onClick={() => onReceipt(o)}
              >
                View receipt
              </button>
              {o.can_cancel && (
                <button
                  className="text-button danger"
                  onClick={() => onCancel(o)}
                >
                  Cancel & release
                </button>
              )}
            </div>
          </section>
        ))}
      </div>
      {!filtered.length && (
        <section className="panel">
          <Empty
            title={
              orders.length
                ? "No matching orders"
                : "Your first commitment starts here"
            }
            description={
              orders.length
                ? "Change the filters or search for a different order."
                : "Approve a supply plan in ASI:One or create a request here."
            }
            action={
              <button
                className="button primary"
                onClick={
                  orders.length
                    ? () => {
                        setSearch("");
                        setFilter("all");
                      }
                    : onNew
                }
              >
                {orders.length ? "Clear filters" : "Create a request"}
              </button>
            }
          />
        </section>
      )}
    </>
  );
}
