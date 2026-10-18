import numpy as np
import pytest

from docassist.config import Settings
from docassist.ingest import chunk_document, extract_document
from docassist.models import Chunk
from docassist.retrieval import SearchIndex


def test_chunking_stays_on_original_pages_and_terminates():
    settings = Settings(chunk_size=100, chunk_overlap=20)
    document = extract_document(
        "pages.txt", (("annual leave " * 60) + "\f" + ("laptop expenses " * 60)).encode(), settings
    )
    chunks = chunk_document(document, settings)
    assert len(chunks) > 2
    assert {c.page for c in chunks} == {1, 2}
    assert len({c.id for c in chunks}) == len(chunks)
    assert all(len(c.text) <= 100 for c in chunks)
    assert all("laptop" not in c.text for c in chunks if c.page == 1)


def test_hybrid_faiss_ranking_and_filters_with_deterministic_encoder():
    pytest.importorskip("faiss")

    class Encoder:
        def encode(self, texts, **_):
            vectors = []
            for text in texts:
                vector = np.array(
                    [1, 0] if "leave" in text or "holiday" in text else [0, 1], dtype="float32"
                )
                vectors.append(vector)
            return np.stack(vectors)

    chunks = [
        Chunk("a:1:0", "a", "a.txt", 1, "Annual leave is eighteen days."),
        Chunk("b:1:0", "b", "b.txt", 1, "Laptop reimbursement is available."),
    ]
    index = SearchIndex(chunks, encoder=Encoder())
    assert index.search("holiday", 1)[0].chunk.document_id == "a"
    assert index.search("holiday", 1, ["b"]) == []
    assert index.search("laptop", 1)[0].chunk.document_id == "b"


def test_empty_vocabulary_is_handled():
    index = SearchIndex([Chunk("a", "a", "a.txt", 1, "the and or the and or")])
    assert index.search("leave", 4) == []


def test_settings_require_explicit_llm_configuration():
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        Settings(llm="openai")
    with pytest.raises(ValueError, match="overlap"):
        Settings(chunk_size=100, chunk_overlap=100)
    with pytest.raises(ValueError, match="between"):
        Settings(min_score=2)
