# Saurav Shahi AI and Python Portfolio

Three personal projects demonstrating document retrieval, natural language classification and predictive machine learning. Each project has runnable code, an API, a browser interface, tests, and documented limitations. These are portfolio applications, not claims of employment experience or production deployment.

| Project | Problem | Implementation |
| --- | --- | --- |
| [SourceDesk document assistant](projects/company-document-assistant/) | Find information in uploaded company documents | Page-preserving PDF ingestion, TF-IDF retrieval, SQLite, optional local embeddings/FAISS and LangChain generation |
| [QueueWise support ticket classifier](projects/support-ticket-classifier/) | Suggest a support queue and collect a human review | TF-IDF, logistic regression, four categories, review fallback, SQLite feedback |
| [RetentionLab customer churn predictor](projects/customer-churn-predictor/) | Explore churn scoring on public telecom data | Group-separated splits, baseline comparison, validation-based model/threshold selection, scoring API and CSV batches |

## Windows quick start

Use Python 3.11 or 3.12. Open a terminal in this repository:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python run.py documents
```

Open http://127.0.0.1:8000 for SourceDesk. Stop it with Ctrl+C, then run another project:

```powershell
.venv\Scripts\python run.py tickets
.venv\Scripts\python run.py churn
```

QueueWise uses http://127.0.0.1:8001 and RetentionLab uses http://127.0.0.1:8002. Run each command in a separate terminal if you want them open together. If Python 3.11 is installed, change the first command to `py -3.11`.

On macOS/Linux, create the environment with `python3 -m venv .venv` and replace `.venv\Scripts\python` with `.venv/bin/python`.

The default modes require no paid API or GPU. SourceDesk has optional model dependencies and optional API-backed generation; its own README explains when document passages leave the local application.

## Check the work

```powershell
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python tools/check_projects.py
```

Measured results are in each project's report or evaluation folder. See [VERIFICATION.md](VERIFICATION.md) for delivered checks and [HOW_TO_EXPLAIN.md](HOW_TO_EXPLAIN.md) for interview preparation.

Metrics have different scopes: the ticket examples are small, fictional and manually authored; the churn dataset is a historical public dataset from one company; the document evaluation uses fictional policies. Do not interpret any of these as production accuracy, user adoption or business savings.

## Code and data licenses

Code is MIT licensed. The UCI Iranian Churn dataset is separately attributed under CC BY 4.0 in its [data notice](projects/customer-churn-predictor/data/DATA_LICENSE.md). Sample policies and ticket examples are fictional original project fixtures.

## Scope

These applications bind to localhost. Add authentication, per-user isolation, proxy/body limits and deployment controls before sharing a live instance publicly. No credentials or private resume files belong in this repository. Model inference does not contact a third party in the default configuration.
