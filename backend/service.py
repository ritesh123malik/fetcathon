import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.db import Database
from backend.models import Requirements
from backend.planner import build_options


def now():
    return datetime.now(timezone.utc).isoformat()


class DomainError(Exception):
    def __init__(self, message: str, status: int = 400):
        self.message, self.status = message, status
        super().__init__(message)


class SupplyService:
    def __init__(self, database: Database):
        self.db = database

    @staticmethod
    def event(conn, entity, kind, message):
        conn.execute(
            "INSERT INTO events(entity_id,kind,message,created_at) VALUES (?,?,?,?)",
            (entity, kind, message, now()),
        )

    def suppliers(self, conn=None):
        if conn is None:
            with self.db.connection() as connection:
                return self.suppliers(connection)
        suppliers = [dict(row) for row in conn.execute("SELECT * FROM suppliers ORDER BY id")]
        for supplier in suppliers:
            supplier["active"] = bool(supplier["active"])
            supplier["inventory"] = [
                dict(row)
                for row in conn.execute(
                    "SELECT product,stock,unit_paise FROM inventory WHERE supplier_id=? ORDER BY product",
                    (supplier["id"],),
                )
            ]
        return suppliers

    def quote(
        self, requirements: Requirements, owner: str, snapshots=None, parent_id=None, conn=None
    ):
        if conn is None:
            with self.db.transaction() as connection:
                return self.quote(requirements, owner, snapshots, parent_id, connection)
        suppliers = snapshots if snapshots is not None else self.suppliers(conn)
        options = build_options(requirements, suppliers)
        quote_id = "RQ-" + uuid4().hex[:10].upper()
        created = now()
        expiry = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        status = "quoted" if options else "unavailable"
        conn.execute(
            "INSERT INTO quotes VALUES (?,?,?,?,?,?,?,?)",
            (
                quote_id,
                owner,
                requirements.model_dump_json(),
                json.dumps(options),
                status,
                created,
                expiry,
                parent_id,
            ),
        )
        self.event(conn, quote_id, "requested", f"Request received: {requirements.title}")
        self.event(
            conn,
            quote_id,
            "sourcing",
            f"Checked {len(suppliers)} supplier inventories against deadline and budget.",
        )
        self.event(
            conn,
            quote_id,
            status,
            f"{len(options)} feasible fulfilment plan(s)."
            if options
            else "No complete plan fits stock, budget, and deadline. Change your constraints and try again.",
        )
        return self.get_quote(quote_id, owner, conn)

    def get_quote(self, quote_id, owner, conn=None):
        if conn is None:
            with self.db.connection() as connection:
                return self.get_quote(quote_id, owner, connection)
        row = conn.execute(
            "SELECT * FROM quotes WHERE id=? AND owner=?", (quote_id, owner)
        ).fetchone()
        if row is None:
            raise DomainError("Request not found.", 404)
        result = dict(row)
        result.pop("owner")
        result["requirements"] = json.loads(result["requirements"])
        result["options"] = json.loads(result["options"])
        result["events"] = [
            dict(e)
            for e in conn.execute("SELECT * FROM events WHERE entity_id=? ORDER BY id", (quote_id,))
        ]
        return result

    def confirm(self, quote_id, option_id, owner):
        # A write lock plus UNIQUE(quote_id) makes retries safe and prevents overselling.
        with self.db.transaction() as conn:
            quote = self.get_quote(quote_id, owner, conn)
            existing = conn.execute("SELECT * FROM orders WHERE quote_id=?", (quote_id,)).fetchone()
            if existing:
                if existing["status"] == "cancelled":
                    raise DomainError(
                        "This order was cancelled. Create a new request to reserve again.", 409
                    )
                if existing["option_id"] != option_id:
                    raise DomainError("This request was already confirmed with another plan.", 409)
                return {"status": "confirmed", "order": self.order_dict(existing), "replayed": True}
            if quote["status"] != "quoted":
                raise DomainError("This quote is no longer open. Create a new request.", 409)
            option = next((o for o in quote["options"] if o["id"] == option_id), None)
            if option is None:
                raise DomainError("Select a valid plan from this request.")
            failure = (
                "The quote expired."
                if datetime.fromisoformat(quote["expires_at"]) < datetime.now(timezone.utc)
                else None
            )
            for line in option["lines"]:
                stock = conn.execute(
                    "SELECT i.*,s.active,s.eta_hours FROM inventory i JOIN suppliers s ON s.id=i.supplier_id WHERE supplier_id=? AND product=?",
                    (line["supplier_id"], line["product"]),
                ).fetchone()
                if (
                    not stock
                    or not stock["active"]
                    or stock["stock"] < line["quantity"]
                    or stock["unit_paise"] != line["unit_paise"]
                    or stock["eta_hours"] != line["eta_hours"]
                ):
                    failure = (
                        f"{line['supplier_name']} changed availability. No inventory was committed."
                    )
                    break
            if failure:
                conn.execute("UPDATE quotes SET status='superseded' WHERE id=?", (quote_id,))
                self.event(conn, quote_id, "recovery", failure)
                replacement = self.quote(
                    Requirements.model_validate(quote["requirements"]),
                    owner,
                    parent_id=quote_id,
                    conn=conn,
                )
                self.event(
                    conn,
                    replacement["id"],
                    "recovery",
                    "Replanned using current inventory. A new approval is required.",
                )
                return {
                    "status": "reapproval_required",
                    "reason": failure,
                    "quote": self.get_quote(replacement["id"], owner, conn),
                }
            for line in option["lines"]:
                conn.execute(
                    "UPDATE inventory SET stock=stock-? WHERE supplier_id=? AND product=?",
                    (line["quantity"], line["supplier_id"], line["product"]),
                )
            order_id = "SR-" + uuid4().hex[:8].upper()
            payload = {
                **option,
                "title": quote["requirements"]["title"],
                "location": quote["requirements"]["location"],
                "reservations": [
                    {"id": "RSV-" + uuid4().hex[:8].upper(), "supplier_id": supplier}
                    for supplier in sorted({line["supplier_id"] for line in option["lines"]})
                ],
            }
            conn.execute(
                "INSERT INTO orders VALUES (?,?,?,?,?,?,?)",
                (order_id, owner, quote_id, option_id, json.dumps(payload), "confirmed", now()),
            )
            conn.execute("UPDATE quotes SET status='confirmed' WHERE id=?", (quote_id,))
            self.event(
                conn,
                quote_id,
                "confirmed",
                f"Order {order_id} committed. {len(payload['reservations'])} inventory reservations created.",
            )
            return {
                "status": "confirmed",
                "order": self.order_dict(
                    conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
                ),
                "replayed": False,
            }

    @staticmethod
    def order_dict(row):
        result = dict(row)
        result.pop("owner")
        result["payload"] = json.loads(result["payload"])
        return result

    def orders(self, owner):
        with self.db.connection() as conn:
            return [
                self.order_dict(r)
                for r in conn.execute(
                    "SELECT * FROM orders WHERE owner=? ORDER BY created_at DESC", (owner,)
                )
            ]

    def cancel_order(self, order_id, owner):
        with self.db.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM orders WHERE id=? AND owner=?", (order_id, owner)
            ).fetchone()
            if row is None:
                raise DomainError("Order not found.", 404)
            if row["status"] != "cancelled":
                for line in json.loads(row["payload"])["lines"]:
                    conn.execute(
                        "UPDATE inventory SET stock=stock+? WHERE supplier_id=? AND product=?",
                        (line["quantity"], line["supplier_id"], line["product"]),
                    )
                conn.execute("UPDATE orders SET status='cancelled' WHERE id=?", (order_id,))
                conn.execute("UPDATE quotes SET status='cancelled' WHERE id=?", (row["quote_id"],))
                self.event(
                    conn,
                    row["quote_id"],
                    "cancelled",
                    f"Order {order_id} cancelled; all inventory released exactly once.",
                )
            return self.order_dict(
                conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
            )

    def update_stock(self, supplier_id, product, stock):
        with self.db.transaction() as conn:
            result = conn.execute(
                "UPDATE inventory SET stock=? WHERE supplier_id=? AND product=?",
                (stock, supplier_id, product),
            )
            if not result.rowcount:
                raise DomainError("Inventory item not found.", 404)
            self.event(
                conn, supplier_id, "inventory", f"Available {product} stock updated to {stock}."
            )

    def availability(self, supplier_id, active):
        with self.db.transaction() as conn:
            if not conn.execute(
                "UPDATE suppliers SET active=? WHERE id=?", (int(active), supplier_id)
            ).rowcount:
                raise DomainError("Supplier not found.", 404)
            self.event(
                conn,
                supplier_id,
                "availability",
                "Supplier accepting orders." if active else "Supplier paused new orders.",
            )

    def dashboard(self, owner, *, operator=False):
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT id,owner FROM quotes ORDER BY created_at DESC LIMIT 100"
                if operator
                else "SELECT id,owner FROM quotes WHERE owner=? ORDER BY created_at DESC LIMIT 100",
                () if operator else (owner,),
            ).fetchall()
            quotes = [self.get_quote(row["id"], row["owner"], conn) for row in rows]
            orders = [
                self.order_dict(row)
                for row in conn.execute(
                    "SELECT * FROM orders ORDER BY created_at DESC"
                    if operator
                    else "SELECT * FROM orders WHERE owner=? ORDER BY created_at DESC",
                    () if operator else (owner,),
                )
            ]
        return {
            "suppliers": self.suppliers(),
            "quotes": quotes,
            "orders": orders,
            "metrics": {
                "confirmed": sum(o["status"] == "confirmed" for o in orders),
                "spend_paise": sum(
                    o["payload"]["total_paise"] for o in orders if o["status"] == "confirmed"
                ),
                "recoveries": sum(q["parent_id"] is not None for q in quotes),
            },
        }

    def operator_owner(self, record_id, *, order=False):
        """Only the authenticated operations API may resolve a customer's record owner."""
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT owner FROM orders WHERE id=?"
                if order
                else "SELECT owner FROM quotes WHERE id=?",
                (record_id,),
            ).fetchone()
            if row is None:
                raise DomainError("Record not found.", 404)
            return row["owner"]

    def session_quote(self, session, quote_id=None):
        with self.db.transaction() as conn:
            if quote_id:
                conn.execute(
                    "INSERT INTO chat_sessions VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET quote_id=excluded.quote_id,updated_at=excluded.updated_at",
                    (session, quote_id, now()),
                )
            row = conn.execute(
                "SELECT quote_id FROM chat_sessions WHERE id=?", (session,)
            ).fetchone()
            return row["quote_id"] if row else None
