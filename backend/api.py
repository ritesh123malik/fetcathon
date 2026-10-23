import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import Settings, settings
from backend.db import Database
from backend.intent import extract_intent
from backend.models import (
    AvailabilityUpdate,
    ChatRequest,
    ConfirmRequest,
    QuoteRequest,
    StockUpdate,
    TrackingUpdate,
)
from backend.service import DomainError, SupplyService


def create_app(config: Settings = settings):
    db = Database(config.database_path)
    service = SupplyService(db)

    @asynccontextmanager
    async def lifespan(app):
        if not config.demo_mode and not config.admin_api_key:
            raise RuntimeError("ADMIN_API_KEY is required outside demo mode.")
        db.initialize(seed=config.demo_mode)
        yield

    app = FastAPI(title="SupplyRescue", version="0.1.0", lifespan=lifespan)
    app.state.service = service

    def authorize(authorization: str = Header(default="")):
        if config.admin_api_key and not secrets.compare_digest(
            authorization, f"Bearer {config.admin_api_key}"
        ):
            raise DomainError("Enter a valid operations access key.", 401)
        return "operations"

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        return JSONResponse(status_code=exc.status, content={"detail": exc.message})

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/config")
    def public_config():
        return {
            "demo_mode": config.demo_mode,
            "ai_connected": bool(config.asi_one_api_key),
            "auth_required": bool(config.admin_api_key),
            "agent_profile_url": config.agent_profile_url,
            "payments_enabled": False,
        }

    @app.get("/api/dashboard")
    def dashboard(owner=Depends(authorize)):
        return service.dashboard(owner, operator=True)

    @app.post("/api/quotes", status_code=201)
    def quote(body: QuoteRequest, owner=Depends(authorize)):
        return service.quote(body.requirements, owner)

    @app.post("/api/intent")
    async def intent(body: ChatRequest, owner=Depends(authorize)):
        requirements, source = await extract_intent(body.message, config)
        return {"requirements": requirements.model_dump(), "source": source}

    @app.get("/api/quotes/{quote_id}")
    def get_quote(quote_id: str, owner=Depends(authorize)):
        return service.get_quote(quote_id, service.operator_owner(quote_id))

    @app.post("/api/quotes/{quote_id}/confirm")
    def confirm(quote_id: str, body: ConfirmRequest, owner=Depends(authorize)):
        return service.confirm(quote_id, body.option_id, service.operator_owner(quote_id))

    @app.post("/api/orders/{order_id}/cancel")
    def cancel(order_id: str, owner=Depends(authorize)):
        return service.cancel_order(order_id, service.operator_owner(order_id, order=True))

    @app.get("/api/orders/{order_id}/tracking")
    def tracking(order_id: str, owner=Depends(authorize)):
        return service.tracking(order_id, service.operator_owner(order_id, order=True))

    @app.post("/api/orders/{order_id}/shipments/{supplier_id}")
    def advance(order_id: str, supplier_id: str, body: TrackingUpdate, owner=Depends(authorize)):
        if not config.demo_mode:
            raise DomainError("Demo fulfilment controls are disabled.", 403)
        return service.advance_shipment(
            order_id,
            service.operator_owner(order_id, order=True),
            supplier_id,
            body.status,
            body.note,
        )

    @app.patch("/api/suppliers/{supplier_id}/availability")
    def availability(supplier_id: str, body: AvailabilityUpdate, owner=Depends(authorize)):
        service.availability(supplier_id, body.active)
        return {"ok": True}

    @app.patch("/api/suppliers/{supplier_id}/inventory/{product}")
    def stock(supplier_id: str, product: str, body: StockUpdate, owner=Depends(authorize)):
        service.update_stock(supplier_id, product, body.stock)
        return {"ok": True}

    frontend = Path(__file__).resolve().parents[1] / "frontend" / "dist"
    if frontend.exists():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="web")
    return app


app = create_app()
