import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient
from ticket_app import create_app
from ticket_model import LABELS, TicketModel, canonical, load_examples


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        yield c


def test_training_and_evaluation_have_distinct_text():
    train, _ = load_examples("training.json")
    evaluation, _ = load_examples("evaluation.json")
    assert len(train) == 60
    assert len(evaluation) == 24
    assert not set(map(canonical, train)) & set(map(canonical, evaluation))


def test_unrelated_words_require_review():
    result = TicketModel().predict("Jupiter quasars nebulae heliosphere")
    assert result["requires_review"]
    assert result["routing"] == "manual_review"
    assert result["matching_terms"] == []


def test_classification_returns_distribution_and_persists(client):
    r = client.post(
        "/api/classify",
        json={"text": "Please send me the invoice for the duplicate billing charge"},
    )
    assert r.status_code == 200
    result = r.json()
    assert result["suggested_category"] == "billing"
    assert set(result["class_probabilities"]) == set(LABELS)
    assert sum(result["class_probabilities"].values()) == pytest.approx(1, abs=0.001)
    assert client.get("/api/tickets").json()["tickets"][0]["id"] == result["id"]


def test_human_review_is_saved_without_changing_original_prediction(client):
    first = client.post(
        "/api/classify", json={"text": "The parcel arrived with a broken item"}
    ).json()
    response = client.post(f"/api/tickets/{first['id']}/review", json={"category": "technical"})
    assert response.status_code == 200
    stored = client.get("/api/tickets").json()["tickets"][0]
    assert stored["suggested_category"] == first["suggested_category"]
    assert stored["reviewed_category"] == "technical"


def test_validation_and_missing_review(client):
    assert client.post("/api/classify", json={"text": "abc"}).status_code == 422
    assert client.post("/api/classify", json={"text": " " * 20}).status_code == 400
    assert (
        client.post("/api/tickets/missing/review", json={"category": "billing"}).status_code == 404
    )
    assert (
        client.post("/api/tickets/missing/review", json={"category": "unknown"}).status_code == 422
    )


def test_measured_report_includes_baseline_and_scope(client):
    report = client.get("/api/metrics").json()
    assert report["macro_f1"] > report["baseline_macro_f1"]
    assert report["evaluation_examples"] == 24
    assert "fictional" in report["dataset"]
    assert client.get("/").status_code == 200
