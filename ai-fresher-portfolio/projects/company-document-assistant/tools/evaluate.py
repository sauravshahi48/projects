"""Evaluate fixture retrieval, never invent model-answer accuracy or business impact."""

import argparse
import json
import statistics
from pathlib import Path
from tempfile import TemporaryDirectory

from docassist.api import ROOT
from docassist.config import Settings
from docassist.models import Question
from docassist.service import Assistant


def evaluate(backend: str):
    fixtures = json.loads(
        (Path(__file__).resolve().parents[1] / "evaluation/questions.json").read_text()
    )
    with TemporaryDirectory() as tmp:
        assistant = Assistant(Settings(data_dir=Path(tmp), retrieval=backend))
        for file in sorted((ROOT / "samples").glob("*.pdf")):
            assistant.add(file.name, file.read_bytes())
        rows = []
        for fixture in fixtures:
            result = assistant.ask(Question(question=fixture["question"]))
            sources = result["sources"]
            is_expected = lambda s: (  # noqa: E731
                s["filename"] == fixture.get("filename") and s["page"] == fixture.get("page")
            )
            rows.append(
                {
                    "question": fixture["question"],
                    "unanswerable": fixture.get("unanswerable", False),
                    "related_unsupported": fixture.get("related_unsupported", False),
                    "expected_page_at_1": bool(sources and is_expected(sources[0])),
                    "expected_page_in_top_4": any(is_expected(s) for s in sources),
                    "expected_text_in_sources": any(
                        fixture.get("answer_contains", "\x00").lower() in s["excerpt"].lower()
                        for s in sources
                    ),
                    "abstained": result["status"] == "not_found",
                    "latency_ms": result["latency_ms"],
                }
            )
    answerable = [r for r in rows if not r["unanswerable"]]
    unknown = [r for r in rows if r["unanswerable"]]
    unrelated = [r for r in unknown if not r["related_unsupported"]]
    related = [r for r in unknown if r["related_unsupported"]]
    return {
        "backend": backend,
        "scope": "Small synthetic sample dataset; retrieval evaluation, not LLM answer correctness.",
        "answerable_questions": len(answerable),
        "unanswerable_questions": len(unknown),
        "page_hit_rate_at_1": sum(r["expected_page_at_1"] for r in answerable) / len(answerable),
        "page_hit_rate_at_4": sum(r["expected_page_in_top_4"] for r in answerable)
        / len(answerable),
        "expected_text_coverage_at_4": sum(r["expected_text_in_sources"] for r in answerable)
        / len(answerable),
        "unanswerable_question_abstention_rate": sum(r["abstained"] for r in unknown)
        / len(unknown),
        "unrelated_topic_abstention_rate": sum(r["abstained"] for r in unrelated) / len(unrelated),
        "related_unsupported_abstention_rate": sum(r["abstained"] for r in related) / len(related),
        "median_query_latency_ms": statistics.median(r["latency_ms"] for r in rows),
        "questions": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["lexical", "hybrid"], default="lexical")
    parser.add_argument("--output", default="evaluation-report.json")
    args = parser.parse_args()
    report = evaluate(args.backend)
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "questions"}, indent=2))
