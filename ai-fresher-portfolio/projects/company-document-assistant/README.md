# SourceDesk — Company Document Assistant

Employees waste time searching through policies and manuals. SourceDesk lets a user upload documents, ask a question, and inspect the original pages supporting a result.

**A runnable Python portfolio project with a FastAPI backend, a responsive browser interface, PDF ingestion, persistent storage, a retrieval baseline, optional semantic search, and optional LangChain generation.**

## Start here on Windows

Install Python **3.11 or 3.12**, extract this project, and open a terminal inside the extracted `company-document-assistant` folder. These commands do not require activating a PowerShell script:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m docassist
```

Open **http://127.0.0.1:8000** in your browser. Click **Load sample documents**, then **Annual leave allowance**. You should see a passage containing **18 days**, attributed to page **2** of the employee handbook. Click **Open source page** to inspect the PDF.

If you have Python 3.11, use `py -3.11` in the first command. Dependencies download during installation; the default app itself needs no model download, GPU, API key, or account.

On macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m docassist
```

## What works

- Upload multiple **PDF, UTF-8 TXT, and Markdown** files.
- Preserve original **PDF page numbers** through chunking and retrieval.
- Search all documents or restrict a question to one document.
- Open source pages and download a text record of the result.
- Detect identical file contents instead of indexing duplicates.
- Keep documents across restarts in **SQLite**; deleting a document removes it from search.
- Reject empty, invalid, encrypted, oversized, and image-only PDFs with useful errors.
- Fall back to retrieved evidence if model generation fails or source references cannot be verified.
- Use built-in API documentation at **http://127.0.0.1:8000/docs**.

The two sample PDFs contain **fictional** Northstar Works policies. They are included for demonstrations and evaluation only.

## Three stages you can explain in an interview

| Stage | Configure | What it demonstrates |
| --- | --- | --- |
| Default offline baseline | No configuration | TF-IDF retrieval, cosine similarity, ingestion, source evidence, SQLite, API design |
| Semantic search | Install `[semantic]`, set `DOCASSIST_RETRIEVAL=hybrid` | Local sentence embeddings, FAISS inner-product search, hybrid ranking |
| Generated answers | Install `[llm]`, configure an API key and model | LangChain structured output, context-limited generation, citation validation and fallback |

**The default mode returns relevant passages, not a generated factual answer.** It can retrieve related text even when the exact answer is absent. It does not claim to understand every question or guarantee answerability.

Semantic retrieval and LLM generation are independent. You can enable either or both. Only the third stage generates prose answers.

### Enable local semantic retrieval

Stop the server with Ctrl+C. On Windows:

```powershell
.venv\Scripts\python -m pip install -e ".[semantic]"
Copy-Item .env.example .env
```

Edit `.env`:

```dotenv
DOCASSIST_RETRIEVAL=hybrid
```

Restart the app. The first start downloads `sentence-transformers/all-MiniLM-L6-v2`, then runs embeddings on the CPU. The optional dependency installs PyTorch and can take substantially more disk space than the baseline. A GPU is not required. Hugging Face access is needed for the first model download.

The hybrid score is `0.55 × semantic similarity + 0.45 × lexical similarity`. Embeddings are normalized, so FAISS inner products correspond to cosine similarity. The scores are **similarities, not confidence probabilities**. The default cutoff is a starting point, not a production-calibrated setting.

### Enable generated answers with LangChain

```powershell
.venv\Scripts\python -m pip install -e ".[llm]"
```

Copy `.env.example` to `.env` if it does not exist. Set:

```dotenv
DOCASSIST_LLM=openai
OPENAI_API_KEY=your_api_key
DOCASSIST_LLM_MODEL=your_available_model_id
```

Choose a model available in your API account that supports JSON-schema structured output. Restart the app. **The question and retrieved passages are sent to the configured provider when you ask a question.** API billing is separate from running the local app. The interface updates its mode and data-use notice when generation is enabled.

Do not commit `.env`. The app reads the key on the server; it never places it in browser JavaScript. No credentials are included in this project.

Generation asks for an answer plus exact supporting quotes. The validator checks that source IDs exist, quotes occur in retrieved passages, and each answer sentence has a source label. Invalid outputs fall back to source passages. These checks validate references; they **do not prove that every claim follows from a quote**. The prompt treats document instructions as untrusted, but prompt injection remains a limitation to test.

## How it is implemented

1. **Ingest:** validate a file and use pypdf to extract readable text page by page.
2. **Chunk:** split each page into overlapping chunks of up to 800 characters, with a 120-character overlap. A chunk never crosses a page.
3. **Index:** build the lexical baseline; optionally encode chunks locally and add vectors to FAISS.
4. **Retrieve:** score the question against chunks, apply document filters and a similarity cutoff, then limit repeated results from a page.
5. **Respond:** show source passages or request a structured answer from LangChain and validate its citations.
6. **Persist:** retain originals and extracted pages in SQLite; rebuild derived indexes on startup and mutations. No pickle loading is used.

The frontend uses HTML, CSS and JavaScript served by the same FastAPI process. It needs no Node build or separate frontend server.

```text
docassist/
  api.py           HTTP routes and static frontend
  config.py        Explicit configuration and limits
  ingest.py        PDF/text extraction and page-preserving chunks
  retrieval.py     TF-IDF baseline and optional embedding/FAISS hybrid
  generation.py    LangChain adapter and citation checks
  service.py       Document lifecycle and question orchestration
  storage.py       SQLite transactions
  static/          Browser interface
  samples/         Two fictional PDFs
tests/             Functional and regression tests
evaluation/        Labeled synthetic questions and measured baseline results
tools/             Evaluation and sample PDF generation
docs/              Interview guide and development roadmap
```

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Mode, retrieval backend and limits |
| GET | `/api/documents` | List indexed files |
| POST | `/api/documents` | Upload multipart `files` |
| POST | `/api/demo` | Load sample PDFs; repeated calls do not duplicate them |
| DELETE | `/api/documents/{id}` | Delete a file and remove it from retrieval |
| GET | `/api/documents/{id}/file` | Open an original file; PDF links include `#page=N` |
| POST | `/api/ask` | Ask with optional document filters |

Example question body:

```json
{"question":"What is the laptop reimbursement limit?","document_ids":null,"top_k":4}
```

`status` is `evidence_only`, `answered`, or `not_found`. Inspect `mode`, `notice`, `sources`, and `latency_ms` instead of treating every response as a model answer.

## Test and evaluate

```powershell
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check .
.venv\Scripts\python tools/evaluate.py --output evaluation-report.json
```

The optional FAISS mechanics test runs when `faiss-cpu` is installed; otherwise pytest explicitly skips it. It uses a deterministic test encoder to verify ranking and filtering, not a downloaded embedding model.

Evaluation reports **correct-page hit rates at 1 and 4**, expected-answer-text coverage, unknown-topic abstention, and median query latency. These are retrieval measurements on a tiny synthetic corpus, not LLM answer accuracy or evidence of business impact. See `evaluation/BASELINE.md` and the accompanying JSON for the run delivered with this project. Build a larger independent evaluation set before claiming general quality.

Live provider calls require your credentials. The generation tests use a deterministic fake model to exercise validation/fallback behavior. When `langchain-openai` is installed, an additional test exercises the actual LangChain/SDK serialization and parsing with fully mocked HTTP. The full optional embedding download and a real paid provider response are not assumed to have been validated by the baseline tests.

## Optional Docker run

```bash
docker build -t sourcedesk .
docker run --rm -p 127.0.0.1:8000:8000 -v sourcedesk-data:/data sourcedesk
```

The container recipe runs the baseline as a non-root user. It is supplied as a deployment starting point; use the Python quick start for the validated local workflow.

## Scope and next steps

This version is a **single-user local portfolio application**, bound to localhost by the Python entry point. It is not an authenticated shared workspace. It supports 40 documents, 80 pages per file, and 10 MB per file. Run **one server process**: the derived in-memory index is not coordinated across multiple workers. PDFs require an extractable text layer; add OCR for scans.

For a public deployment, implement user authentication, per-user document isolation, request body limits at the proxy, rate limiting, background ingestion and worker timeouts. The built-in limits reduce accidental misuse; they are not a sandbox for hostile PDF parsing. SQLite is not encrypted and deleted content may remain in database free pages or backups; deletion here means removal from the app and search, not forensic erasure.

Other improvements: query rewriting, reranking, a larger held-out evaluation set, stronger claim verification, multilingual evaluation, and incremental embeddings instead of rebuilding the full index after each change.

## Learning and job applications

Read **`docs/INTERVIEW_GUIDE.md`** for a demonstration script, technical questions and honest resume wording. Follow **`docs/BUILD_PLAN.md`** to understand and extend the code. Publish your own repository and demo after you can explain the pipeline and reproduce the evaluation. This package does not publish or deploy anything automatically.

## Official references

- [FastAPI file uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [pypdf text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)
- [Sentence Transformers semantic search](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html)
- [FAISS documentation](https://faiss.ai/)
- [LangChain ChatOpenAI integration](https://docs.langchain.com/oss/python/integrations/chat/openai)

## License

MIT. The fictional sample policies are part of this project, not scraped employer documents.
