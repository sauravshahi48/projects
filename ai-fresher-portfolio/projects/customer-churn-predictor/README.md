# RetentionLab customer churn predictor

A personal machine learning project using the public UCI Iranian Churn dataset. It compares models, selects a decision threshold on validation data, and exposes individual and CSV batch scoring through FastAPI.

## Run

Follow the portfolio root README, then run `python run.py churn` with the virtual environment's Python. Alternatively, from this folder:

```powershell
python -m pip install -r requirements.txt
python churn_app.py
```

Open http://127.0.0.1:8002. Model training runs locally during startup and is cached in memory. The bundled CSV means no account or runtime data download is needed.

## Dataset and feature decisions

UCI provides 3,150 anonymous customer records. Predictors aggregate the first nine months and the churn outcome is recorded at the end of twelve months. See [the source](https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset) and [data attribution](data/DATA_LICENSE.md).

This version uses nine activity/plan fields. It excludes `Status` as a strong proxy worth treating cautiously, excludes the derived `Customer Value`, and excludes `Age` and `Age Group` to focus on service activity. These are project design choices, not a claim that UCI's documented features are invalid. Raw CSV bytes are retained; the source URL and hash are in `data/source.json`.

## Evaluation design

1. Remove exact duplicate raw rows.
2. Hash the selected feature vectors and keep identical vectors within one partition.
3. Create seeded, stratified group partitions for training, validation and test.
4. Fit preprocessing on training only. Compare a prior-probability dummy, logistic regression and random forest.
5. Select the learned model by validation average precision.
6. Choose its threshold by validation F1 over a fixed threshold grid.
7. Evaluate the selected model on the test partition without refitting on validation.

`reports/evaluation.json` contains the measured sizes, scores, confusion matrix, threshold, feature choices and limitations. Reproduce it with `python churn_model.py`.

Average precision is reported as its own metric; it is not interchangeable with a trapezoidal PR-AUC calculation. The target is imbalanced, so accuracy alone is insufficient. Scores are not calibrated probabilities. No customer retention action is automatically taken.

## Interface and API

- Nine validated activity inputs and a sample anonymous profile.
- A model score compared with the validation-selected threshold.
- Global feature importance, explicitly distinguished from individual or causal explanations.
- CSV template and batch scoring with a 1 MB / 2,000-row limit. Input is processed in memory, not stored.
- `GET /api/schema`, `GET /api/metrics`, `POST /api/predict`, `GET /api/example.csv`, `POST /api/batch`.

## Checks and limitations

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover partition separation, baseline comparison, required feature validation, target exclusion at inference, CSV scoring and malformed input.

This is a historical dataset from one company. Random group separation does not establish performance on new companies or future periods. Input records outside observed ranges deserve extra scrutiny. A deployment needs authentication, rate limits, monitoring and independent prospective evaluation. No business savings, customers served or production use are claimed.
