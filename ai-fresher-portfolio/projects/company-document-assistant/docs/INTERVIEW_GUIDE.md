# Explain the project before putting it on your resume

## A 45-second introduction

“SourceDesk helps users find information inside uploaded company policies. I use Python and FastAPI for the backend, pypdf for text extraction, and SQLite for persistence. I preserve the page number of every chunk so a user can inspect each result. The baseline uses TF-IDF search and displays evidence. An optional hybrid adds local sentence embeddings and FAISS. An optional LangChain adapter generates structured answers with source labels and exact supporting quotes. If generation fails citation checks, the app falls back to passages. I evaluate retrieval on labeled questions instead of treating a fluent response as proof of correctness.”

Use “I built” only after you have studied, run, understood and meaningfully worked on this implementation. Explain any assistance you used honestly if asked. Do not claim employment experience for a personal project.

## A three-minute demo

1. Start with an empty knowledge base and load the two fictional sample PDFs.
2. Ask “How many days of annual leave do employees receive?” Show the 18-day passage and open Employee Handbook page 2.
3. Ask “What is the laptop reimbursement limit?” Show the INR 60,000 passage from Expense Policy page 1.
4. Change the document filter to the handbook and ask about laptop reimbursement. Explain how document filtering works.
5. Ask “What is the orbital velocity of Neptune?” Show that unrelated questions do not receive an invented answer.
6. Upload the same PDF again and show duplicate detection. Restart and demonstrate persistence.
7. Explain the distinction between the offline evidence mode and optional generated answers. Demonstrate the generated mode only if you have configured and checked it yourself.

## Questions to prepare

| Interview question | What to explain |
| --- | --- |
| Is the default app generative AI? | No. It is an offline retrieval baseline that returns passages. Optional LangChain generation adds an LLM step. |
| What is RAG? | Retrieve relevant document context before asking an LLM to answer from that context. Retrieval quality and answer quality need separate evaluation. |
| Why keep a lexical baseline? | It is inexpensive and inspectable. It helps measure whether semantic retrieval actually improves a task. |
| What does an embedding do? | It represents text as a vector. Similar meanings can be close even when the wording differs. |
| Why FAISS IndexFlatIP? | With normalized vectors, inner products give cosine similarity. Flat search is simple and appropriate for a small corpus, but scales linearly. |
| Why overlapping chunks? | To reduce information loss at boundaries. Overlap also increases index size and repeated results. |
| Why not cross page boundaries? | A citation can point to one actual page. Cross-page context needs richer citation metadata. |
| What does the similarity score mean? | A ranking signal. It is not a probability that an answer is correct. |
| How are hallucinations handled? | Context-limited prompting, explicit abstention instructions, exact quote/source validation, and evidence fallback reduce some errors. They do not eliminate false claims. |
| Can a valid quote still support a wrong answer? | Yes. Reference validity is different from entailment. A stronger system evaluates claims against evidence. |
| What is prompt injection here? | A document may contain instructions directed at the model. The app treats text as untrusted data and provides no execution tools, but instruction-based defenses are imperfect. |
| What if a PDF is scanned? | pypdf cannot recover image text. The app asks for OCR rather than silently pretending the file was indexed. |
| How do you prevent data leakage in evaluation? | Separate development examples from a larger held-out evaluation set, avoid tuning thresholds on the reported holdout, and document dataset limitations. |
| How does deletion work? | Remove the SQLite row, rebuild the derived index, and stop serving the document. This is logical deletion, not guaranteed disk erasure. |
| What limits scaling? | Full index rebuilds, synchronous parsing, a local database and per-process memory. Add background jobs, incremental indexes and shared storage as scope grows. |

## Resume bullets after you reproduce the work

- Developed a Python/FastAPI document assistant with PDF ingestion, page-level source references, document filtering and persistent SQLite storage.
- Implemented an offline TF-IDF retrieval baseline and evaluated correct-page retrieval and abstention using labeled synthetic questions.
- Added functional tests for ingestion failures, duplicate uploads, document deletion, persistence, citation validation and provider failure fallback.

If you enable, understand and test semantic retrieval yourself:

- Extended retrieval with local sentence embeddings and FAISS, and compared the hybrid against the lexical baseline on a held-out question set.

If you enable and test generation yourself:

- Integrated LangChain structured generation with source-label and quote validation, plus evidence fallback for unverifiable responses.

Add only the metrics from **your own reproducible run**, with the dataset size and scope. Do not claim generic “99% accuracy,” fabricated users, time saved, or production deployment.

## What to show recruiters

An accessible repository, installation instructions, one short video, a running demo if available, and an evaluation report with known limitations. Make your own meaningful extension, such as OCR ingestion or a held-out multilingual evaluation, and explain the tradeoffs.
