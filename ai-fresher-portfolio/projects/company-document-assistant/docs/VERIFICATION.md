# Delivered verification

Verified on 18 October 2026, using Python 3.12.14 on Linux.

- **32 pytest tests passed.** This run included the optional real FAISS mechanics test with a deterministic encoder and the actual LangChain/SDK adapter test with mocked HTTP.
- **Ruff checks and formatting passed.** JavaScript passed Node's syntax check.
- **Real HTTP smoke passed:** application startup, frontend assets, sample loading, correct PDF pages, unrelated-topic abstention, text upload and deletion.
- **Headless Chromium interface checks passed:** sample loading, annual-leave and laptop questions, page citation links, result download, unrelated-topic abstention, file upload, deletion and zero JavaScript page errors.
- Desktop (1440 × 1050) and mobile (390 × 844) screens were rendered and inspected. The mobile result had no horizontal page overflow.
- Both sample PDFs were rendered and their five pages visually inspected.
- A wheel was built and checked for inclusion of the browser assets and both sample PDFs.
- The 24-question synthetic evaluation is included in `evaluation/baseline-results.json`; `evaluation/BASELINE.md` explains the results and limitations, including unsupported questions about related policies.

This does not include a downloaded sentence-transformer inference run, a real paid model response, execution on Windows, a Docker build, a hosted deployment, or a run of the supplied GitHub Actions workflow. The Windows instructions and optional deployment configuration are provided for the next stage of your work.

The package contains no API credentials or user documents. Only the fictional sample policies are included. See `evaluation/verified-versions.txt` for the package versions used during checks.
