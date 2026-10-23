import pytest

from backend.db import Database
from backend.models import Requirements
from backend.service import SupplyService


@pytest.fixture
def service(tmp_path):
    db = Database(str(tmp_path / "test.sqlite3"))
    db.initialize(seed=True)
    return SupplyService(db)


@pytest.fixture
def requirements():
    return Requirements(
        items=[{"product": "notebook", "quantity": 60}, {"product": "pen", "quantity": 60}],
        budget_paise=450000,
        deadline_hours=24,
    )
