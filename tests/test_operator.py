from fastapi.testclient import TestClient

from backend.api import create_app
from backend.config import Settings


def test_operator_sees_chat_orders_but_requires_auth(tmp_path, requirements):
    app = create_app(
        Settings(
            _env_file=None,
            database_path=str(tmp_path / "operator.sqlite3"),
            admin_api_key="private-operator-key",
        )
    )
    with TestClient(app) as client:
        service = app.state.service
        quote = service.quote(requirements, "separate-chat-user")
        order = service.confirm(quote["id"], "option-1", "separate-chat-user")["order"]
        assert client.get("/api/dashboard").status_code == 401
        headers = {"Authorization": "Bearer private-operator-key"}
        assert (
            client.get("/api/dashboard", headers=headers).json()["orders"][0]["id"] == order["id"]
        )
        assert (
            client.post(f"/api/orders/{order['id']}/cancel", headers=headers).json()["status"]
            == "cancelled"
        )
        assert (
            client.post(
                f"/api/quotes/{quote['id']}/confirm",
                json={"option_id": "option-1"},
                headers=headers,
            ).status_code
            == 409
        )
