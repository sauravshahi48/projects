# Saurav Shahi AI and Python Portfolio

Three current personal projects for entry-level AI/ML and Python roles, with runnable applications, APIs, tests and reproducible evaluation.

| Project | What it demonstrates |
| --- | --- |
| [SourceDesk Company Document Assistant](ai-fresher-portfolio/projects/company-document-assistant/) | PDF ingestion, page citations, document retrieval, SQLite and optional FAISS/LangChain integrations |
| [QueueWise Support Ticket Classifier](ai-fresher-portfolio/projects/support-ticket-classifier/) | TF-IDF, logistic regression, review fallback, human feedback and local ticket storage |
| [RetentionLab Customer Churn Predictor](ai-fresher-portfolio/projects/customer-churn-predictor/) | Public UCI data, grouped evaluation, model comparison, validated individual and CSV scoring |

Start with the [portfolio setup guide](ai-fresher-portfolio/README.md). The default applications need no paid API or GPU.

## Run the portfolio

```powershell
git clone https://github.com/sauravshahi48/projects.git
cd projects/ai-fresher-portfolio
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python run.py documents
```

Use `tickets` or `churn` instead of `documents` to run the other applications. Setup commands for Python 3.11 and other operating systems are in the guide.

## Verification and scope

[47 local tests passed](ai-fresher-portfolio/VERIFICATION.md), including optional checks present in the delivered environment. The browser interfaces were checked at desktop and mobile sizes. Read the project reports for dataset provenance, measured results and limitations. Ticket examples and company policies are fictional; churn measurements come from one historical public dataset. These projects do not claim employment experience, production deployment or business savings.

[Interview notes](ai-fresher-portfolio/HOW_TO_EXPLAIN.md) and [LinkedIn project descriptions](ai-fresher-portfolio/LINKEDIN_PROJECTS.md) are included.

## Earlier backend projects

- [Global Store Expansion Platform](global-store-expansion-platform/)
- [Localized Checkout and Payment Routing Simulator](localized-checkout-payment-routing-simulator/)
- [Product Information Extraction Pipeline](product-information-extraction-pipeline/)
