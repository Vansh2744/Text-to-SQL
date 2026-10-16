import json
import os
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp()
os.environ.update(
    APP_ENV="test", AUTH_MODE="dev", DATABASE_URL=f"sqlite:///{_tmp}/test.db",
    UPLOAD_DIR=f"{_tmp}/uploads", RATE_LIMIT_PER_MINUTE="1000",
)

import pytest
from fastapi.testclient import TestClient

import app.models
from app.api.deps import get_llm
from app.db.session import Base, engine
from app.main import app

SAMPLE = Path(__file__).resolve().parents[2] / "sample-data" / "sales.csv"
REVENUE_SQL = ("SELECT region, sum(quantity * unit_price) AS revenue FROM data "
               "GROUP BY region ORDER BY revenue DESC")


class FakeLLM:
    """Scripted provider: SQL replies are popped from `sql_replies` (last one repeats)."""

    def __init__(self):
        self.sql_replies = [{"sql": REVENUE_SQL, "visualization": {"type": "bar", "x": "region",
                                                                    "y": ["revenue"]}}]
        self.prompts: list[str] = []
        self.explain_fails = False

    def complete(self, system: str, user: str) -> str:
        if system.startswith("You explain"):
            if self.explain_fails:
                return "garbage"
            return json.dumps({"explanation": "North leads in revenue."})
        self.prompts.append(user)
        reply = self.sql_replies.pop(0) if len(self.sql_replies) > 1 else self.sql_replies[0]
        return json.dumps(reply)


@pytest.fixture
def llm():
    return FakeLLM()


@pytest.fixture
def client(llm):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    app.dependency_overrides[get_llm] = lambda: llm
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


def H(user="alice"):
    return {"X-Dev-User": user}


@pytest.fixture
def dataset(client):
    with SAMPLE.open("rb") as f:
        r = client.post("/api/v1/datasets/upload", files={"file": ("sales.csv", f, "text/csv")},
                        headers=H())
    assert r.status_code == 201, r.text
    return r.json()
