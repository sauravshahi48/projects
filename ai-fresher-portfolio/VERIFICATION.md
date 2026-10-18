# Verification on 18 October 2026

All three project test suites were run from this portfolio tree with Python 3.12.14 on Linux:

| Project | Result |
| --- | --- |
| SourceDesk | 32 tests passed, including optional FAISS mechanics and mocked LangChain/SDK integration |
| QueueWise | 6 tests passed |
| RetentionLab | 9 tests passed |
| Total | 47 tests passed |

The optional SourceDesk checks require their dependencies; a base-only installation explicitly skips those optional tests. No real paid model call or downloaded embedding-model inference is claimed by this verification.

Ruff checks and formatting passed for Python code. Both new interfaces passed JavaScript syntax checks and live headless Chromium checks: ticket classification, human review persistence, churn scoring, desktop/mobile layouts and no JavaScript page errors. The 390-pixel mobile layouts had no horizontal page overflow. Rendered desktop and mobile pages were inspected. SourceDesk has separate delivered browser/PDF verification in its own docs.

QueueWise measured macro F1 of 0.958 on 24 manually authored fictional evaluation tickets; the majority baseline was 0.100. This is a tiny related-vocabulary demonstration set, not a generalization benchmark. At the demo threshold, 58.3% of these examples required manual review.

RetentionLab removed 300 exact duplicates from 3,150 public dataset rows and used partitions of 1,707 / 574 / 569 rows. The validation-selected random forest and threshold 0.600 produced test average precision 0.864, ROC AUC 0.970, precision 0.740 and recall 0.831. Results apply to this historical dataset and split only. Full reports, hashes, feature choices and limitations are included.

The Windows setup commands and GitHub Actions workflow are provided but were not executed on those platforms. No repository upload, public deployment or LinkedIn publication is implied by local verification.
