"""Group-separated train/validation/test evaluation on the public UCI churn dataset."""

import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).parent
FEATURES = {
    "call_failures": "Call Failure",
    "complaints": "Complains",
    "subscription_months": "Subscription Length",
    "charge_band": "Charge Amount",
    "seconds_of_use": "Seconds of Use",
    "call_frequency": "Frequency of use",
    "sms_frequency": "Frequency of SMS",
    "distinct_numbers": "Distinct Called Numbers",
    "tariff_plan": "Tariff Plan",
}
DESCRIPTIONS = {
    "call_failures": "Call failures",
    "complaints": "Complaint recorded (0 or 1)",
    "subscription_months": "Subscription length in months",
    "charge_band": "Charge band (ordinal 0 to 9)",
    "seconds_of_use": "Total seconds of calls",
    "call_frequency": "Total call count",
    "sms_frequency": "Total SMS count",
    "distinct_numbers": "Distinct called numbers",
    "tariff_plan": "Tariff (1 pay as you go, 2 contractual)",
}
EXCLUDED = ["Status", "Customer Value", "Age", "Age Group"]


@dataclass
class Bundle:
    model: Pipeline
    report: dict
    example: dict
    schema: list[dict]
    split_groups: tuple[set, set, set]


def metrics(y, probability, threshold):
    predicted = (probability >= threshold).astype(int)
    return {
        "average_precision": float(average_precision_score(y, probability)),
        "roc_auc": float(roc_auc_score(y, probability)),
        "precision": float(precision_score(y, predicted, zero_division=0)),
        "recall": float(recall_score(y, predicted, zero_division=0)),
        "f1": float(f1_score(y, predicted, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y, predicted)),
        "confusion_matrix": confusion_matrix(y, predicted, labels=[0, 1]).tolist(),
    }


@lru_cache(maxsize=1)
def train_model():
    path = ROOT / "data" / "customer_churn.csv"
    frame = pd.read_csv(path)
    frame.columns = [re.sub(r"\s+", " ", c.strip()) for c in frame.columns]
    original_count = len(frame)
    frame = frame.drop_duplicates().reset_index(drop=True)
    x = frame[list(FEATURES.values())].rename(columns={v: k for k, v in FEATURES.items()})
    x = x.apply(pd.to_numeric, errors="raise")
    y = frame["Churn"].astype(int)
    groups = pd.util.hash_pandas_object(x, index=False).to_numpy()

    # Identical feature vectors remain in one partition, even if other raw fields differ.
    outer = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    trainval, test = next(outer.split(x, y, groups))
    inner = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=43)
    train_local, validation_local = next(
        inner.split(x.iloc[trainval], y.iloc[trainval], groups[trainval])
    )
    train, validation = trainval[train_local], trainval[validation_local]
    group_sets = (set(groups[train]), set(groups[validation]), set(groups[test]))
    if any(group_sets[a] & group_sets[b] for a, b in [(0, 1), (0, 2), (1, 2)]):
        raise ValueError("Feature-vector groups crossed partitions.")

    candidates = {
        "dummy_prior": DummyClassifier(strategy="prior"),
        "logistic_regression": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=42
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=180,
            min_samples_leaf=4,
            class_weight="balanced",
            random_state=42,
            n_jobs=1,
        ),
    }
    models, validation_scores = {}, {}
    for name, classifier in candidates.items():
        model = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("classifier", classifier),
            ]
        )
        model.fit(x.iloc[train], y.iloc[train])
        probability = model.predict_proba(x.iloc[validation])[:, 1]
        validation_scores[name] = float(average_precision_score(y.iloc[validation], probability))
        models[name] = model
    # Choose a learned model and threshold on validation only; test is never used to tune.
    selected = max((n for n in models if n != "dummy_prior"), key=validation_scores.get)
    model = models[selected]
    val_probability = model.predict_proba(x.iloc[validation])[:, 1]
    thresholds = np.linspace(0.1, 0.9, 33)
    threshold = float(
        max(thresholds, key=lambda t: f1_score(y.iloc[validation], val_probability >= t))
    )
    test_probability = model.predict_proba(x.iloc[test])[:, 1]
    classifier = model.named_steps["classifier"]
    importance = (
        classifier.feature_importances_
        if hasattr(classifier, "feature_importances_")
        else np.abs(classifier.coef_[0])
    )
    signals = sorted(
        [
            {"feature": name, "importance": float(value)}
            for name, value in zip(FEATURES, importance)
        ],
        key=lambda d: -d["importance"],
    )
    report = {
        "dataset": "UCI Iranian Churn",
        "doi": "10.24432/C5JW3Z",
        "license": "CC BY 4.0",
        "csv_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "original_rows": original_count,
        "deduplicated_rows": len(frame),
        "removed_duplicate_rows": original_count - len(frame),
        "features": list(FEATURES),
        "excluded_features": EXCLUDED,
        "split": {
            "train": len(train),
            "validation": len(validation),
            "test": len(test),
        },
        "class_prevalence": {
            name: float(y.iloc[index].mean())
            for name, index in [
                ("train", train),
                ("validation", validation),
                ("test", test),
            ]
        },
        "identical_feature_groups_disjoint": True,
        "validation_average_precision": validation_scores,
        "selected_model": selected,
        "threshold": threshold,
        "threshold_selection": "Maximum validation F1 over 33 fixed candidate thresholds; no refit on validation.",
        "test_metrics": metrics(y.iloc[test], test_probability, threshold),
        "dummy_test_metrics": metrics(
            y.iloc[test], models["dummy_prior"].predict_proba(x.iloc[test])[:, 1], 0.5
        ),
        "global_feature_signals": signals,
        "limitations": "Historical single-company dataset and random grouped holdout. No prospective validation, causal effect, or retention savings are established. Scores are not calibrated.",
    }
    example = {name: int(value) for name, value in x.iloc[test[0]].items()}
    schema = [
        {
            "name": name,
            "label": DESCRIPTIONS[name],
            "min": int(x[name].min()),
            "max": int(x[name].max()),
        }
        for name in FEATURES
    ]
    return Bundle(
        model=model,
        report=report,
        example=example,
        schema=schema,
        split_groups=group_sets,
    )


def predict_customer(bundle, record):
    data = pd.DataFrame([record], columns=list(FEATURES))
    probability = float(bundle.model.predict_proba(data)[0, 1])
    warnings = [
        f"{f['name']} is outside the observed dataset range."
        for f in bundle.schema
        if record[f["name"]] < f["min"] or record[f["name"]] > f["max"]
    ]
    return {
        "churn_score": round(probability, 4),
        "above_threshold": probability >= bundle.report["threshold"],
        "threshold": bundle.report["threshold"],
        "model": bundle.report["selected_model"],
        "warnings": warnings,
        "notice": "A model estimate on a historical dataset, not a calibrated probability or a guaranteed customer outcome.",
    }


if __name__ == "__main__":
    bundle = train_model()
    folder = ROOT / "reports"
    folder.mkdir(exist_ok=True)
    (folder / "evaluation.json").write_text(
        json.dumps(bundle.report, indent=2) + "\n", encoding="utf-8"
    )
    pd.DataFrame([bundle.example]).to_csv(ROOT / "data" / "example_customers.csv", index=False)
    print(json.dumps(bundle.report, indent=2))
