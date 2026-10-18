# Delivered baseline evaluation

Run on 18 October 2026 with Python 3.12.14, using the included two fictional company PDFs (five pages total). The questions are visible synthetic fixtures, not a held-out benchmark. Generation is disabled for this report.

| Measurement | Observed result |
| --- | --- |
| Questions with an answer in the PDFs | 16 |
| Questions without an answer | 8 (4 unrelated topics, 4 related but unsupported) |
| Correct page ranked first, answerable questions | 100% (16/16) |
| Correct page among top four, answerable questions | 100% (16/16) |
| Expected text present in retrieved evidence | 100% (16/16) |
| Abstention on unrelated topics | 100% (4/4) |
| Abstention on related but unsupported questions | 0% (0/4) |
| Overall abstention on questions without an answer | 50% (4/8) |
| Median retrieval/orchestration time | 0.3 ms on this machine and tiny corpus |

The related-but-unsupported result is a limitation: lexical similarity retrieves related policy text even if it does not establish the requested answer. The app labels these results as evidence, not generated answers. A score cutoff alone is not an answerability classifier.

The latency excludes file parsing, indexing, startup and HTTP/browser overhead. It cannot be extrapolated to large corpora, model calls or another machine.

The fixture uses simple examples drawn from a very small known corpus. These results demonstrate that the pipeline works on this fixture; they are not evidence of general accuracy. Add an independent dataset and evaluate semantic retrieval and generated-answer correctness separately.

Reproduce:

```powershell
.venv\Scripts\python tools/evaluate.py --output evaluation-report.json
```

Full question-level results are in `baseline-results.json`.
