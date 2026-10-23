export type Product = "notebook" | "pen" | "lanyard";
export interface Requirements {
  items: { product: Product; quantity: number }[];
  budget_paise: number;
  deadline_hours: number;
  location: string;
  title: string;
}
export interface Supplier {
  id: string;
  name: string;
  area: string;
  eta_hours: number;
  active: boolean;
  color: string;
  initials: string;
  inventory: { product: Product; stock: number; unit_paise: number }[];
}
export interface Allocation {
  supplier_id: string;
  supplier_name: string;
  product: Product;
  quantity: number;
  unit_paise: number;
  eta_hours: number;
}
export interface Option {
  id: string;
  label: string;
  total_paise: number;
  eta_hours: number;
  supplier_count: number;
  lines: Allocation[];
}
export interface TimelineEvent {
  id: number;
  kind: string;
  message: string;
  created_at: string;
}
export interface Quote {
  id: string;
  requirements: Requirements;
  options: Option[];
  status: string;
  created_at: string;
  expires_at: string;
  parent_id: string | null;
  events: TimelineEvent[];
}
export interface Order {
  id: string;
  quote_id: string;
  option_id: string;
  status: string;
  created_at: string;
  payload: Option & {
    title: string;
    location: string;
    reservations: { id: string; supplier_id: string }[];
  };
}
export interface Dashboard {
  suppliers: Supplier[];
  quotes: Quote[];
  orders: Order[];
  metrics: { confirmed: number; spend_paise: number; recoveries: number };
}
export interface Config {
  demo_mode: boolean;
  ai_connected: boolean;
  auth_required: boolean;
  agent_profile_url: string;
  payments_enabled: boolean;
}
export type ConfirmResult =
  | { status: "confirmed"; order: Order; replayed: boolean }
  | { status: "reapproval_required"; reason: string; quote: Quote };
