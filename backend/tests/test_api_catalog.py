import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from fastapi.testclient import TestClient
from app.main import app


def test_agent_catalog_and_chart_contract():
    client = TestClient(app)
    agents = client.get("/api/agents")
    chart = client.get("/api/charts/rankings?ranking=CONSUMO")
    assert agents.status_code == 200
    assert {item["id"] for item in agents.json()["agents"]} >= {"ask-to", "ranking-engine"}
    assert chart.status_code == 200
    body = chart.json()
    assert body["type"] == "bar"
    assert len(body["data"]["labels"]) == 12
    assert len(body["data"]["datasets"][0]["data"]) == 12
