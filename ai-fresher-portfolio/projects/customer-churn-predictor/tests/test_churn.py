import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from churn_app import create_app
from churn_model import FEATURES, train_model
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    with TestClient(create_app()) as c:
        yield c


def test_identical_customer_feature_groups_do_not_cross_partitions():
    bundle = train_model()
    train, validation, test = bundle.split_groups
    assert not train & validation
    assert not train & test
    assert not validation & test
    assert set(bundle.report["features"]) == set(FEATURES)
    assert "Status" in bundle.report["excluded_features"]


def test_baseline_comparison_and_reproducible_split(client):
    report = client.get("/api/metrics").json()
    assert sum(report["split"].values()) == report["deduplicated_rows"]
    assert (
        report["test_metrics"]["average_precision"]
        > report["dummy_test_metrics"]["average_precision"]
    )
    assert 0.1 <= report["threshold"] <= 0.9
    assert len(report["test_metrics"]["confusion_matrix"]) == 2


def test_prediction_validates_inputs_and_has_scope(client):
    example = client.get("/api/schema").json()["example"]
    result = client.post("/api/predict", json=example)
    assert result.status_code == 200
    assert 0 <= result.json()["churn_score"] <= 1
    assert "historical" in result.json()["notice"]
    assert client.post("/api/predict", json={**example, "charge_band": -1}).status_code == 422
    assert client.post("/api/predict", json={**example, "Churn": 1}).status_code == 422


def test_batch_csv_roundtrip(client):
    sample = client.get("/api/example.csv").content
    response = client.post("/api/batch", files={"file": ("customers.csv", sample, "text/csv")})
    assert response.status_code == 200
    assert "churn_score" in response.text
    assert "above_threshold" in response.text


@pytest.mark.parametrize("data", [b"", b"wrong,columns\n1,2", b"\xff\xfe", b"x" * 1_000_001])
def test_bad_batch_files_have_clear_errors(client, data):
    response = client.post("/api/batch", files={"file": ("bad.csv", data)})
    assert response.status_code == 400


def test_app_frontend_is_available(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Churn" in response.text
