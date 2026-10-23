import { useCallback, useEffect, useState } from "react";
import {
  ArrowDownLeft,
  ArrowRight,
  ArrowUpRight,
  Bell,
  Check,
  ChevronRight,
  Clock3,
  Download,
  ExternalLink,
  LoaderCircle,
  MapPin,
  Package,
  Plus,
  Radio,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Truck,
  Users,
  Zap,
} from "lucide-react";
import { api, money, time } from "./api";
import { Empty, Modal, Notice, Sidebar, Status, type Page } from "./components";
import RequestForm from "./RequestForm";
import QuoteReview, { Receipt } from "./QuoteReview";
import Suppliers from "./Suppliers";
import type { Config, Dashboard, Order, Quote } from "./types";

const pageTitles: Record<Page, string> = {
  overview: "Overview",
  requests: "Rescue requests",
  suppliers: "Supplier network",
  orders: "Orders & receipts",
  guide: "Demo & setup guide",
};
export default function App() {
  const [page, setPage] = useState<Page>("overview");
  const [config, setConfig] = useState<Config | null>(null);
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");
  const [newRequest, setNewRequest] = useState(false);
  const [quote, setQuote] = useState<Quote | null>(null);
  const [receipt, setReceipt] = useState<Order | null>(null);
  const [cancel, setCancel] = useState<Order | null>(null);
  const [cancelBusy, setCancelBusy] = useState(false);
  const [search, setSearch] = useState("");
  const [key, setKey] = useState("");
  const [needsAuth, setNeedsAuth] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const refresh = useCallback(async () => {
    setRefreshing(true);
    try {
      setData(await api<Dashboard>("/dashboard"));
      setError("");
      setNeedsAuth(false);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRefreshing(false);
    }
  }, []);
  useEffect(() => {
    api<Config>("/config")
      .then((c) => {
        setConfig(c);
        if (c.auth_required && !sessionStorage.getItem("supplyrescue-key"))
          setNeedsAuth(true);
        else void refresh();
      })
      .catch((e) => setError(e.message));
  }, [refresh]);
  const closeNew = useCallback(() => setNewRequest(false), []);
  const closeQuote = useCallback(() => setQuote(null), []);
  const closeReceipt = useCallback(() => setReceipt(null), []);
  const closeCancel = useCallback(() => setCancel(null), []);
  const quotes = (data?.quotes || []).filter((q) =>
    `${q.id} ${q.requirements.title}`
      .toLowerCase()
      .includes(search.toLowerCase()),
  );
  const activity = (data?.quotes || [])
    .flatMap((q) =>
      q.events.map((e) => ({ ...e, title: q.requirements.title })),
    )
    .sort((a, b) => b.id - a.id)
    .slice(0, 4);
  function created(q: Quote) {
    setNewRequest(false);
    setQuote(q);
    void refresh();
  }
  async function cancelOrder() {
    if (!cancel) return;
    setCancelBusy(true);
    try {
      await api(`/orders/${cancel.id}/cancel`, "POST");
      setCancel(null);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setCancelBusy(false);
    }
  }
  const requestsTable = (limit?: number) => (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>REQUEST</th>
            <th>STATUS</th>
            <th>BUDGET</th>
            <th>DEADLINE</th>
            <th aria-label="Actions" />
          </tr>
        </thead>
        <tbody>
          {quotes.slice(0, limit).map((q) => (
            <tr key={q.id}>
              <td>
                <button className="request-link" onClick={() => setQuote(q)}>
                  <span className="request-icon">
                    <Package size={17} />
                  </span>
                  <span>
                    <strong>{q.requirements.title}</strong>
                    <small>
                      {q.id} ·{" "}
                      {q.requirements.items.reduce((n, i) => n + i.quantity, 0)}{" "}
                      items
                    </small>
                  </span>
                </button>
              </td>
              <td>
                <Status status={q.status} />
              </td>
              <td>{money(q.requirements.budget_paise)}</td>
              <td>
                <span className="deadline">
                  <Clock3 size={13} />
                  {q.requirements.deadline_hours} hours
                </span>
              </td>
              <td>
                <button
                  className="icon-button"
                  aria-label={`Review ${q.id}`}
                  onClick={() => setQuote(q)}
                >
                  <ArrowUpRight size={17} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
  return (
    <div className="app">
      <Sidebar
        page={page}
        onPage={(p) => {
          setPage(p);
          setSearch("");
        }}
        onNew={() => setNewRequest(true)}
        config={config}
      />
      <main>
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <ChevronRight size={14} />
            <strong>{pageTitles[page]}</strong>
          </div>
          <div className="topbar-right">
            <span className="environment">
              <i />
              {config?.demo_mode ? "DEMO ENVIRONMENT" : "PRIVATE OPERATIONS"}
            </span>
            <button
              className="icon-button"
              title="Refresh workspace"
              aria-label="Refresh workspace"
              onClick={() => void refresh()}
            >
              <RefreshCw size={17} className={refreshing ? "spin" : ""} />
            </button>
            <button
              className="icon-button"
              aria-label="View recent activity"
              onClick={() => {
                setPage("overview");
                setTimeout(
                  () =>
                    document
                      .getElementById("activity")
                      ?.scrollIntoView({ behavior: "smooth" }),
                  30,
                );
              }}
            >
              <Bell size={18} />
            </button>
            <span className="avatar small-avatar">OP</span>
          </div>
        </header>
        <div className="main-content">
          {error && (
            <div className="error banner" role="alert">
              {error}
              <button onClick={() => void refresh()}>Retry</button>
              {config?.auth_required && (
                <button onClick={() => setNeedsAuth(true)}>
                  Enter access key
                </button>
              )}
            </div>
          )}
          {page === "overview" ? (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">YOUR OPERATIONS, UNDER CONTROL</div>
                  <h1>A little less last-minute.</h1>
                  <p>
                    Good things happen when your backup plan is already in
                    motion.
                  </p>
                </div>
                <button
                  className="button secondary"
                  onClick={() => setNewRequest(true)}
                >
                  <Plus size={16} />
                  New request
                </button>
              </div>
              <section className="hero">
                <div className="hero-copy">
                  <span className="hero-badge">
                    <Zap size={12} fill="currentColor" /> FROM INTENT TO ACTION
                  </span>
                  <h2>
                    Supplier fell through?
                    <br />
                    We’ll take it from here.
                  </h2>
                  <p>
                    One request. A coordinated supplier network.
                    <br />
                    The right supplies, within your budget and deadline.
                  </p>
                  <button
                    className="button lime"
                    onClick={() => setNewRequest(true)}
                  >
                    Start a rescue <ArrowRight size={17} />
                  </button>
                  <div className="hero-footnote">
                    <ShieldCheck size={13} />
                    You approve. We coordinate. Every step is recorded.
                  </div>
                </div>
                <div className="network-art" aria-hidden="true">
                  <div className="orbit orbit-one" />
                  <div className="orbit orbit-two" />
                  <div className="art-line line-one" />
                  <div className="art-line line-two" />
                  <div className="art-line line-three" />
                  <div className="art-center">
                    <Zap size={38} fill="currentColor" />
                  </div>
                  <div className="art-node node-one">
                    <span className="node-icon">
                      <Package size={22} />
                    </span>
                    <div>
                      <strong>Stock located</strong>
                      <small>Across your supplier network</small>
                    </div>
                    <span className="node-check">
                      <Check size={13} />
                    </span>
                  </div>
                  <div className="art-node node-two">
                    <span className="node-icon">
                      <Users size={21} />
                    </span>
                    <div>
                      <strong>A plan that fits</strong>
                      <small>Budget + deadline matched</small>
                    </div>
                  </div>
                  <div className="art-node node-three">
                    <span className="node-icon">
                      <ShieldCheck size={22} />
                    </span>
                    <div>
                      <strong>Ready when you are</strong>
                      <small>Review. Approve. Confirm.</small>
                    </div>
                  </div>
                  <span className="art-spark spark-one">+</span>
                  <span className="art-spark spark-two">+</span>
                </div>
              </section>
              <section className="metrics">
                <Metric
                  icon={<Radio size={19} />}
                  label="Open rescue requests"
                  value={String(
                    data?.quotes.filter((q) => q.status === "quoted").length ||
                      0,
                  )}
                  detail="Awaiting your review"
                />
                <Metric
                  icon={<Users size={19} />}
                  label="Available suppliers"
                  value={`${data?.suppliers.filter((s) => s.active).length || 0}`}
                  detail="Connected to this workspace"
                />
                <Metric
                  icon={<Package size={19} />}
                  label="Confirmed orders"
                  value={String(data?.metrics.confirmed || 0)}
                  detail="Inventory successfully reserved"
                />
                <Metric
                  icon={<TrendingUp size={19} />}
                  label="Committed order value"
                  value={money(data?.metrics.spend_paise || 0)}
                  detail="No payment collected"
                />
              </section>
              <div className="overview-grid">
                <section className="panel requests-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>
                        Recent rescue requests{" "}
                        <span className="count">
                          {data?.quotes.length || 0}
                        </span>
                      </h2>
                      <p>A clear view of what’s in motion.</p>
                    </div>
                    <button
                      className="text-button"
                      onClick={() => setPage("requests")}
                    >
                      View all <ArrowRight size={14} />
                    </button>
                  </div>
                  {quotes.length ? (
                    requestsTable(4)
                  ) : (
                    <Empty
                      title="Your next rescue starts here."
                      description="Create a request and we’ll find a complete supply plan. No back-and-forth calls required."
                      action={
                        <button
                          className="button secondary"
                          onClick={() => setNewRequest(true)}
                        >
                          <Plus size={16} />
                          Create your first request
                        </button>
                      }
                    />
                  )}
                  <div className="panel-bottom">
                    <ShieldCheck size={14} /> Every confirmation rechecks stock.
                    No partial orders.
                  </div>
                </section>
                <section className="panel network-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>On your side</h2>
                      <p>Your supplier network</p>
                    </div>
                    <span className="online-count">
                      {data?.suppliers.filter((s) => s.active).length || 0}{" "}
                      available
                    </span>
                  </div>
                  <div className="supplier-mini-list">
                    {data?.suppliers.map((s) => (
                      <div className="supplier-mini" key={s.id}>
                        <span className={`supplier-avatar ${s.color}`}>
                          {s.initials}
                        </span>
                        <div>
                          <strong>{s.name}</strong>
                          <small>
                            <MapPin size={11} />
                            {s.area} <span>·</span> {s.eta_hours}h
                          </small>
                        </div>
                        <span
                          className={`availability-dot ${s.active ? "" : "off"}`}
                          title={s.active ? "Available" : "Paused"}
                        />
                      </div>
                    ))}
                  </div>
                  <button
                    className="network-link"
                    onClick={() => setPage("suppliers")}
                  >
                    Manage supplier network <ArrowUpRight size={15} />
                  </button>
                </section>
              </div>
              <div className="bottom-grid">
                <section className="panel activity-panel" id="activity">
                  <div className="panel-heading">
                    <h2>Latest activity</h2>
                    <span className="eyebrow">EXECUTION LOG</span>
                  </div>
                  {activity.length ? (
                    <div className="activity-list">
                      {activity.map((e) => (
                        <div className="activity-row" key={e.id}>
                          <span
                            className={`activity-icon ${e.kind === "confirmed" ? "green" : ""}`}
                          >
                            {e.kind === "confirmed" ? (
                              <Check size={15} />
                            ) : (
                              <ArrowDownLeft size={15} />
                            )}
                          </span>
                          <div>
                            <p>{e.message}</p>
                            <small>{e.title}</small>
                          </div>
                          <time>{time(e.created_at)}</time>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="activity-placeholder">
                      <Clock3 size={21} />
                      <div>
                        <strong>A quiet workspace is a good start.</strong>
                        <p>
                          Quotes, confirmations, and recoveries will appear
                          here.
                        </p>
                      </div>
                    </div>
                  )}
                </section>
                <section className="conversation-card">
                  <span className="conversation-icon">
                    <Sparkles size={20} />
                  </span>
                  <div>
                    <span className="eyebrow">
                      ONE CONVERSATION. ALL THE COORDINATION.
                    </span>
                    <h3>Already in ASI:One?</h3>
                    <p>
                      Find supplies, compare plans, and confirm an order without
                      leaving your chat.
                    </p>
                    <button
                      className="text-button"
                      onClick={() => setPage("guide")}
                    >
                      Explore the agent workflow <ArrowUpRight size={14} />
                    </button>
                  </div>
                </section>
              </div>
            </>
          ) : (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">SUPPLYRESCUE WORKSPACE</div>
                  <h1>{pageTitles[page]}</h1>
                  <p>
                    {page === "suppliers"
                      ? "Live inventory and availability. You stay in control."
                      : page === "orders"
                        ? "Every commitment, with the receipts to prove it."
                        : page === "requests"
                          ? "From a supply gap to a plan you can count on."
                          : "A transparent demo. A clear path to ASI:One."}
                  </p>
                </div>
                {page === "requests" && (
                  <button
                    className="button primary"
                    onClick={() => setNewRequest(true)}
                  >
                    <Plus size={16} />
                    New request
                  </button>
                )}
              </div>
              {page === "requests" && (
                <section className="panel">
                  <div className="panel-heading">
                    <h2>All requests</h2>
                    <label className="search">
                      <Search size={15} />
                      <input
                        placeholder="Search requests…"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                      />
                    </label>
                  </div>
                  {quotes.length ? (
                    requestsTable()
                  ) : (
                    <Empty
                      title="No requests found"
                      description="Try a different search or create a new rescue request."
                    />
                  )}
                </section>
              )}
              {page === "suppliers" && (
                <Suppliers
                  suppliers={data?.suppliers || []}
                  onChange={() => void refresh()}
                />
              )}{" "}
              {page === "orders" && (
                <div className="orders-list">
                  {data?.orders.length ? (
                    data.orders.map((o) => (
                      <section className="panel order-card" key={o.id}>
                        <div className="order-heading">
                          <span className="request-icon">
                            <Truck size={23} />
                          </span>
                          <div>
                            <h3>{o.payload.title}</h3>
                            <small>
                              {o.id} ·{" "}
                              {new Date(o.created_at).toLocaleDateString(
                                "en-IN",
                              )}
                            </small>
                          </div>
                          <Status status={o.status} />
                        </div>
                        <div className="order-details">
                          <div>
                            <span>Order value</span>
                            <strong>{money(o.payload.total_paise)}</strong>
                          </div>
                          <div>
                            <span>Suppliers</span>
                            <strong>
                              {o.payload.supplier_count} confirmed
                            </strong>
                          </div>
                          <div>
                            <span>Fulfilment location</span>
                            <strong>{o.payload.location}</strong>
                          </div>
                        </div>
                        <div className="order-footer">
                          <button
                            className="button secondary small"
                            onClick={() => setReceipt(o)}
                          >
                            <Download size={14} />
                            View receipt
                          </button>
                          {o.status === "confirmed" && (
                            <button
                              className="text-button danger"
                              onClick={() => setCancel(o)}
                            >
                              Cancel & release inventory
                            </button>
                          )}
                        </div>
                      </section>
                    ))
                  ) : (
                    <section className="panel">
                      <Empty
                        title="No orders yet"
                        description="Approved rescue plans become confirmed orders here."
                        action={
                          <button
                            className="button primary"
                            onClick={() => setNewRequest(true)}
                          >
                            Create a request <ArrowRight size={15} />
                          </button>
                        }
                      />
                    </section>
                  )}
                </div>
              )}
              {page === "guide" && (
                <Guide config={config} onNew={() => setNewRequest(true)} />
              )}
            </>
          )}
          <footer className="footer">
            <span>
              <Zap size={12} /> SupplyRescue · A better plan B.
            </span>
            <span>
              {config?.demo_mode
                ? "Demo suppliers. Persistent inventory. No real purchases."
                : "Private supplier operations."}
            </span>
          </footer>
        </div>
      </main>
      {!data && !error && !needsAuth && (
        <div className="loading-pill">
          <LoaderCircle className="spin" size={16} />
          Connecting workspace…
        </div>
      )}
      {newRequest && (
        <RequestForm onClose={closeNew} onCreated={created} config={config} />
      )}{" "}
      {quote && (
        <QuoteReview
          initial={quote}
          onClose={closeQuote}
          onChange={() => void refresh()}
        />
      )}{" "}
      {receipt && (
        <Modal title="Order receipt" onClose={closeReceipt}>
          <div className="modal-body">
            <Notice>
              {receipt.status === "cancelled"
                ? "This order was cancelled. Inventory has been released."
                : "Reservation receipt. No payment has been collected."}
            </Notice>
            <Receipt order={receipt} />
          </div>
        </Modal>
      )}
      {cancel && (
        <Modal title="Release this order?" onClose={closeCancel}>
          <div className="modal-body">
            <p>
              Cancel <strong>{cancel.id}</strong> and return all reserved items
              to available inventory? This action is recorded.
            </p>
            <div className="dialog-actions">
              <button className="button secondary" onClick={closeCancel}>
                Keep order
              </button>
              <button
                className="button primary"
                disabled={cancelBusy}
                onClick={() => void cancelOrder()}
              >
                Cancel order
              </button>
            </div>
          </div>
        </Modal>
      )}
      {needsAuth && (
        <Modal
          title="Connect your workspace"
          onClose={() => setNeedsAuth(false)}
        >
          <form
            className="modal-body"
            onSubmit={(e) => {
              e.preventDefault();
              sessionStorage.setItem("supplyrescue-key", key);
              void refresh();
            }}
          >
            <label className="field">
              Operations access key
              <input
                type="password"
                required
                value={key}
                onChange={(e) => setKey(e.target.value)}
              />
            </label>
            <p className="muted">
              Stored for this browser session only. Ask your workspace operator
              for the key.
            </p>
            {error && <p className="error">{error}</p>}
            <button className="button primary">Connect workspace</button>
          </form>
        </Modal>
      )}
    </div>
  );
}

function Metric({
  icon,
  label,
  value,
  detail,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <article className="metric">
      <div className="metric-top">
        <span>{label}</span>
        <span className="metric-icon">{icon}</span>
      </div>
      <strong>{value}</strong>
      <p>{detail}</p>
    </article>
  );
}

function Guide({
  config,
  onNew,
}: {
  config: Config | null;
  onNew: () => void;
}) {
  return (
    <div className="guide-grid">
      <section className="panel guide-card">
        <span className="section-icon">
          <Zap size={23} />
        </span>
        <h2>Run the full rescue story</h2>
        <ol>
          <li>
            <strong>Create a request.</strong> Try 60 notebooks and 60 pens,
            ₹4,500 budget, within 24 hours.
          </li>
          <li>
            <strong>Review the allocation.</strong> Compare price, supplier
            split, and fulfilment time.
          </li>
          <li>
            <strong>Introduce a disruption.</strong> Close the quote, pause
            Campus Paper Co. in Supplier network, then reopen the request.
          </li>
          <li>
            <strong>Confirm and recover.</strong> The engine rejects the stale
            allocation and proposes a new one. Review and approve it.
          </li>
          <li>
            <strong>Inspect the receipt.</strong> Check reservation IDs and
            inventory. Cancelling releases inventory exactly once.
          </li>
        </ol>
        <button className="button primary" onClick={onNew}>
          Try a rescue <ArrowRight size={16} />
        </button>
      </section>
      <section className="panel guide-card">
        <span className="section-icon">
          <Sparkles size={23} />
        </span>
        <h2>Native to ASI:One</h2>
        <p>
          The web console is for operations. The hackathon’s primary workflow
          lives entirely in ASI:One using Agent Chat Protocol and Interactive
          Cards.
        </p>
        <div className="connection-row">
          <span>ASI:One intent extraction</span>
          <Status
            status={config?.ai_connected ? "confirmed" : "Not configured"}
          />
        </div>
        <div className="connection-row">
          <span>Agentverse profile</span>
          <Status
            status={
              config?.agent_profile_url ? "Configured" : "Pending registration"
            }
          />
        </div>
        <div className="connection-row">
          <span>Payment collection</span>
          <span className="muted">Not enabled</span>
        </div>
        <Notice>
          Demo mode uses explicitly labelled suppliers. The local parser is not
          an LLM. No real purchases or payments occur.
        </Notice>
        <p>
          See the repository’s deployment guide to configure credentials, run
          the agent network, and register your agent. Registration and a public
          shared chat are required before submission.
        </p>
        <a
          className="button secondary"
          href="https://agentverse.ai"
          target="_blank"
          rel="noreferrer"
        >
          Open Agentverse <ExternalLink size={14} />
        </a>
      </section>
    </div>
  );
}
