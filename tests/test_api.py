from fastapi.testclient import TestClient

from backend.api import create_app
from backend.config import Settings


def test_api_full_flow_and_auth(tmp_path, requirements):
    app = create_app(
        Settings(
            _env_file=None,
            database_path=str(tmp_path / "api.sqlite3"),
            demo_mode=True,
            admin_api_key="test-key",
        )
    )
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/dashboard").status_code == 401
        headers = {"Authorization": "Bearer test-key"}
        response = client.post(
            "/api/quotes", headers=headers, json={"requirements": requirements.model_dump()}
        )
        assert response.status_code == 201
        quote = response.json()
        confirmed = client.post(
            f"/api/quotes/{quote['id']}/confirm", headers=headers, json={"option_id": "option-1"}
        )
        assert confirmed.json()["status"] == "confirmed"
        order_id = confirmed.json()["order"]["id"]
        assert (
            client.post(f"/api/orders/{order_id}/cancel", headers=headers).json()["status"]
            == "cancelled"
        )
        assert (
            client.patch(
                "/api/suppliers/campus/inventory/notebook", headers=headers, json={"stock": -1}
            ).status_code
            == 422
        )


def test_intent_demo_and_validation(tmp_path):
    app = create_app(
        Settings(_env_file=None, database_path=str(tmp_path / "demo.sqlite3"), demo_mode=True)
    )
    with TestClient(app) as client:
        assert client.post("/api/intent", json={"message": "buy stuff"}).status_code == 400
        response = client.post(
            "/api/intent", json={"message": "60 notebooks and 60 pens under ₹4,500 within 24 hours"}
        )
        assert response.json()["source"] == "demo_parser"
        assert response.json()["requirements"]["budget_paise"] == 450000
