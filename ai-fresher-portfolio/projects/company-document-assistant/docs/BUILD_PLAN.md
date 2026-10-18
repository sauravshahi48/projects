# A seven-session learning plan

You can run the complete project immediately. Use this plan to learn enough to explain it and make it your own. Adjust the pace to your Python comfort level.

| Session | Read and build | Evidence you understand it |
| --- | --- | --- |
| 1 | Run the app, load the PDFs, read `api.py` and the API docs | Send an `/api/ask` request and explain the returned fields |
| 2 | Read `ingest.py`; inspect page extraction and chunk boundaries | Add a regression test proving a citation stays on its original page |
| 3 | Read `retrieval.py`; learn TF-IDF, vectors and cosine similarity | Change a question's wording and explain why lexical retrieval changes |
| 4 | Read `storage.py` and `service.py` | Demonstrate duplicate detection, restart persistence and deletion |
| 5 | Run evaluation; inspect failures as well as successes | Add at least 15 independent questions, including related-but-unanswerable ones |
| 6 | Install semantic retrieval if resources allow; optionally enable generation | Compare search modes using the same questions; distinguish reference validity from factual correctness |
| 7 | Make a meaningful improvement, document it and record a demo | Explain the change, tradeoff and measured result without reading notes |

## Suggested extensions

Choose one to complete, not every idea at once:

1. **OCR:** add scanned-PDF support with explicit page mapping and tests.
2. **Evaluation:** collect at least 50 independently labeled questions, including paraphrases, unsupported policy questions and contradictory sources.
3. **Search quality:** compare lexical, semantic and hybrid retrieval; add a reranker and measure changes in correct-page retrieval and latency.
4. **Ingestion efficiency:** cache embeddings by chunk content hash instead of re-encoding all documents after each mutation.
5. **Multi-user deployment:** add authenticated users and separate document ownership at storage and query boundaries.

Keep one baseline. Record what changed, why you expected improvement, and whether the data supported it.
