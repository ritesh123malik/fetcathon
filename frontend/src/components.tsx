import { useEffect, useRef, type ReactNode } from "react";
import {
  ArrowUpRight,
  Box,
  Check,
  CircleHelp,
  LayoutDashboard,
  Package,
  Plus,
  Radio,
  ShieldCheck,
  Sparkles,
  Users,
  X,
  Zap,
} from "lucide-react";
import type { Config } from "./types";

export type Page = "overview" | "requests" | "suppliers" | "orders" | "guide";
export function Sidebar({
  page,
  onPage,
  onNew,
  config,
}: {
  page: Page;
  onPage: (p: Page) => void;
  onNew: () => void;
  config: Config | null;
}) {
  const links = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "requests", label: "Rescue requests", icon: Radio },
    { id: "suppliers", label: "Supplier network", icon: Users },
    { id: "orders", label: "Orders & receipts", icon: Package },
  ] as const;
  return (
    <aside className="sidebar">
      <a
        href="#"
        className="brand"
        onClick={(e) => {
          e.preventDefault();
          onPage("overview");
        }}
      >
        <span className="brand-icon">
          <Zap size={23} fill="currentColor" />
        </span>
        SupplyRescue<span className="brand-dot">.</span>
      </a>
      <div className="workspace">
        <span className="workspace-avatar">S</span>
        <div>
          <strong>Campus workspace</strong>
          <small>Operations console</small>
        </div>
        <span className="workspace-dot" />
      </div>
      <button className="button primary sidebar-new" onClick={onNew}>
        <Plus size={17} /> New rescue request
      </button>
      <div className="nav-label">WORKSPACE</div>
      <nav>
        {links.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => onPage(id)}
            className={`nav-item ${page === id ? "selected" : ""}`}
          >
            <Icon size={18} />
            {label}
            {page === id && <span className="nav-indicator" />}
          </button>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="asi-box">
          <span className="asi-symbol">
            <Sparkles size={18} />
          </span>
          <strong>Built for ASI:One</strong>
          <p>
            Your entire rescue workflow.
            <br />
            One conversation.
          </p>
          {config?.agent_profile_url ? (
            <a href={config.agent_profile_url} target="_blank" rel="noreferrer">
              Open agent <ArrowUpRight size={14} />
            </a>
          ) : (
            <button onClick={() => onPage("guide")}>
              Connection guide <ArrowUpRight size={14} />
            </button>
          )}
        </div>
        <button
          className={`nav-item ${page === "guide" ? "selected" : ""}`}
          onClick={() => onPage("guide")}
        >
          <CircleHelp size={18} />
          Demo & setup guide
        </button>
        <div className="account">
          <span className="avatar">OP</span>
          <div>
            <strong>Operations team</strong>
            <small>
              {config?.demo_mode ? "Demo workspace" : "Private workspace"}
            </small>
          </div>
          <ShieldCheck size={17} />
        </div>
      </div>
    </aside>
  );
}

export function Modal({
  title,
  children,
  onClose,
  wide = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const bodyOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    ref.current?.focus();
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab") {
        const items = ref.current?.querySelectorAll<HTMLElement>(
          "button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href]",
        );
        if (!items?.length) return;
        const first = items[0],
          last = items[items.length - 1];
        if (
          e.shiftKey &&
          (document.activeElement === first ||
            document.activeElement === ref.current)
        ) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", handler);
    return () => {
      document.body.style.overflow = bodyOverflow;
      document.removeEventListener("keydown", handler);
      previous?.focus();
    };
  }, [onClose]);
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={ref}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`modal ${wide ? "wide" : ""}`}
      >
        <header className="modal-header">
          <div>
            <span className="eyebrow">SUPPLYRESCUE WORKSPACE</span>
            <h2>{title}</h2>
          </div>
          <button
            className="icon-button"
            onClick={onClose}
            aria-label="Close dialog"
          >
            <X size={20} />
          </button>
        </header>
        {children}
      </div>
    </div>
  );
}

export function Status({ status }: { status: string }) {
  const label: Record<string, string> = {
    quoted: "Ready for review",
    confirmed: "Confirmed",
    cancelled: "Cancelled",
    unavailable: "No matching plan",
    superseded: "Replanned",
  };
  return (
    <span className={`status ${status}`}>
      <span />
      {label[status] || status}
    </span>
  );
}
export function Empty({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <Box size={28} />
      </span>
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  );
}
export function Notice({
  children,
  success = false,
}: {
  children: ReactNode;
  success?: boolean;
}) {
  return (
    <div className={`notice ${success ? "success" : ""}`} role="status">
      {success ? <Check size={17} /> : <ShieldCheck size={17} />}
      <span>{children}</span>
    </div>
  );
}
