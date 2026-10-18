# QueueWise support ticket classifier

A personal NLP project that suggests a support queue, exposes model signals, provides a response template, and records a human correction. It does not contact customers or send messages.

## Run

From the portfolio root, follow the root README and run `python run.py tickets` with your virtual environment's Python. Alternatively, inside this folder:

```powershell
python -m pip install -r requirements.txt
python ticket_app.py
```

Open http://127.0.0.1:8001. The API docs are at `/docs`.

## Model and evaluation

- TF-IDF word and bigram features with logistic regression.
- Four categories: account, billing, orders and technical.
- 60 manually authored fictional training examples and 24 separate fictional evaluation examples.
- A most-frequent-class baseline, macro F1, accuracy, per-class metrics and the fraction requiring manual review.
- An uncalibrated score threshold of 0.55 and zero-known-feature check route uncertain text to review.
- Weighted matching terms expose linear-model signals; they are not a causal explanation or proof of correctness.

Reproduce the report with `python ticket_model.py`. Read `reports/evaluation.json` for the actual run. Do not interpret a high score on this small authored set as production performance. The same four domains and related vocabulary occur in both files; exact-text overlap is checked, but a larger independent dataset is required.

The review threshold was chosen as a demonstrative rule, not tuned on a real validation dataset. Out-of-domain detection is limited: an unfamiliar request containing familiar words may still receive a strong score. Human review and broader evaluation remain important.

## API

| Endpoint | Purpose |
| --- | --- |
| `POST /api/classify` | Analyze a `text` field and save its original prediction locally |
| `GET /api/tickets` | View recent local tickets and review labels |
| `POST /api/tickets/{id}/review` | Save a category correction without overwriting the original suggestion |
| `GET /api/metrics` | Inspect the measured evaluation and scope |

SQLite files live in `.data/`, which is excluded from git. This single-user local prototype has no authentication or data retention controls; do not use real confidential support tickets for a public demo.

## Checks

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover data separation, probability output, persistence, human feedback, unfamiliar text, invalid input, and baseline comparison. The browser interface uses text nodes rather than injecting submitted ticket text as HTML.
