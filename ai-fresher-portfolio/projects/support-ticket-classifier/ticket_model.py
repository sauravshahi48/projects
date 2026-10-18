"""Small, reproducible NLP baseline with separate fictional training/evaluation examples."""

import json
import re
from pathlib import Path

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).parent
LABELS = ("account", "billing", "orders", "technical")
REPLIES = {
    "account": "Thanks for contacting account support. Please describe the sign-in or profile issue. Do not share your password or verification codes.",
    "billing": "Thanks for contacting billing support. We will review the charge or invoice. Please use the approved support channel for any payment references.",
    "orders": "Thanks for contacting order support. Please provide your order reference in the approved support channel so the team can review the delivery or return.",
    "technical": "Thanks for reporting the technical issue. Please describe the steps that reproduce it, your app version, and the error message without including secrets.",
}


def load_examples(filename):
    dataset = json.loads((ROOT / "data" / filename).read_text(encoding="utf-8"))
    if set(dataset) != set(LABELS):
        raise ValueError("The dataset must include all four support categories.")
    rows = [(text, label) for label, texts in dataset.items() for text in texts]
    return [r[0] for r in rows], [r[1] for r in rows]


def canonical(text):
    return re.sub(r"\W+", " ", text.lower()).strip()


class TicketModel:
    def __init__(self, review_threshold=0.55):
        self.review_threshold = review_threshold
        train_x, train_y = load_examples("training.json")
        test_x, test_y = load_examples("evaluation.json")
        if set(map(canonical, train_x)) & set(map(canonical, test_x)):
            raise ValueError("Identical text must not occur in both training and evaluation.")
        self.pipeline = Pipeline(
            [
                ("vectorizer", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
                ("classifier", LogisticRegression(C=4, max_iter=2000, random_state=42)),
            ]
        )
        self.pipeline.fit(train_x, train_y)
        predicted = self.pipeline.predict(test_x)
        baseline = DummyClassifier(strategy="most_frequent").fit(
            np.zeros((len(train_y), 1)), train_y
        )
        dummy = baseline.predict(np.zeros((len(test_y), 1)))
        self.report = {
            "dataset": "Manually authored fictional English tickets; not customer production data.",
            "train_examples": len(train_x),
            "evaluation_examples": len(test_x),
            "classes": list(self.pipeline.classes_),
            "review_threshold": self.review_threshold,
            "model": "TF-IDF + Logistic Regression",
            "accuracy": float(accuracy_score(test_y, predicted)),
            "macro_f1": float(f1_score(test_y, predicted, average="macro")),
            "baseline_macro_f1": float(f1_score(test_y, dummy, average="macro", zero_division=0)),
            "manual_review_rate": float(
                np.mean(self.pipeline.predict_proba(test_x).max(axis=1) < review_threshold)
            ),
            "classification_report": classification_report(
                test_y, predicted, output_dict=True, zero_division=0
            ),
            "limitations": "Tiny authored evaluation set with related vocabulary; scores do not establish real-world generalization. Probabilities are not calibrated.",
        }

    def predict(self, text):
        text = text.strip()
        vectorizer = self.pipeline.named_steps["vectorizer"]
        vector = vectorizer.transform([text])
        probabilities = self.pipeline.predict_proba([text])[0]
        index = int(probabilities.argmax())
        label = str(self.pipeline.classes_[index])
        score = float(probabilities[index])
        review = score < self.review_threshold or vector.nnz == 0
        coefficients = self.pipeline.named_steps["classifier"].coef_[index]
        weights = vector.toarray()[0] * coefficients
        terms = vectorizer.get_feature_names_out()
        matching = [
            {"term": str(terms[i]), "weight": round(float(weights[i]), 4)}
            for i in np.argsort(-weights)[:5]
            if weights[i] > 0
        ]
        return {
            "suggested_category": label,
            "model_probability": round(score, 4),
            "requires_review": bool(review),
            "routing": "manual_review" if review else label,
            "class_probabilities": {
                str(c): round(float(p), 4) for c, p in zip(self.pipeline.classes_, probabilities)
            },
            "matching_terms": matching,
            "draft_reply": "A support agent should review this request before choosing a reply."
            if review
            else REPLIES[label],
            "notice": "Draft only. Nothing is sent to a customer. Scores are uncalibrated model probabilities.",
        }


if __name__ == "__main__":
    model = TicketModel()
    folder = ROOT / "reports"
    folder.mkdir(exist_ok=True)
    (folder / "evaluation.json").write_text(
        json.dumps(model.report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(model.report, indent=2))
