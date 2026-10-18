# LinkedIn project descriptions

These entries describe personal projects created in October 2026. Add each project's actual GitHub location after publication; no repository URL is invented here.

## SourceDesk Company Document Assistant

Personal portfolio application for exploring company documents with inspectable source evidence. Implemented PDF/TXT ingestion, page-preserving chunks, TF-IDF search, document filters, duplicate detection and SQLite persistence. Results link to original source pages. Optional integrations add local embeddings with FAISS and LangChain structured generation with source-quote validation and fallback. The default mode retrieves passages without a paid API. Includes 32 automated tests and a small synthetic evaluation with documented limitations.

Skills: Python, FastAPI, SQLite, Information Retrieval, scikit-learn, LangChain.

## QueueWise Support Ticket Classifier

Personal NLP project that suggests billing, account, order or technical support categories using TF-IDF and logistic regression. The interface shows class scores and weighted matching terms, flags uncertain requests for human review, provides draft response templates, and saves category feedback while retaining the original prediction. Uses 60 fictional training tickets and 24 separate fictional evaluation examples with a majority baseline. The small authored evaluation is a demonstration, not a production accuracy claim. No customer messages are sent automatically.

Skills: Python, Natural Language Processing, scikit-learn, FastAPI, SQLite, Model Evaluation.

## RetentionLab Customer Churn Predictor

Personal machine learning project using the public UCI Iranian Churn dataset. Removed duplicate rows, kept identical input-vector groups within one partition, and compared dummy, logistic-regression and random-forest models. Selected the model and threshold on validation data. The selected model achieved average precision 0.864 on 569 held-out records in the delivered run. Implemented a FastAPI dashboard, validated individual scoring, CSV batch scoring and global feature signals. Historical single-company results do not establish prospective accuracy or customer retention savings.

Skills: Python, pandas, scikit-learn, Random Forest, FastAPI, Model Evaluation.

## Profile placement

Use the Projects section for individual entries and attach verified repository links. Feature the published portfolio repository if a single entry is preferred. These are personal projects, not positions in the Experience section. The repository contains project code and public datasets only; keep personal resume documents out of public commits unless you explicitly want them public.
