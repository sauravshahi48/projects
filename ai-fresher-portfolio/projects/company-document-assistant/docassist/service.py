import logging
from collections import Counter
from threading import RLock
from time import perf_counter

from .config import Settings
from .generation import LangChainGenerator, validate_citations
from .ingest import DocumentError, chunk_document, extract_document
from .models import Document, Hit, Question
from .retrieval import Retriever
from .storage import Store

logger = logging.getLogger(__name__)


class Assistant:
    def __init__(self, settings: Settings, generator=None):
        self.settings = settings
        self.lock = RLock()
        self.store = Store(settings.data_dir)
        self.documents = self.store.load()
        self.retriever = Retriever(settings.retrieval, settings.embedding_model)
        self.index = self._build(self.documents)
        self.generator = generator
        if self.generator is None and settings.llm != "off":
            self.generator = LangChainGenerator(settings)

    def _build(self, documents: list[Document]):
        chunks = [c for document in documents for c in chunk_document(document, self.settings)]
        return self.retriever.build(chunks)

    def _metadata(self, document: Document):
        return {
            "id": document.id,
            "name": document.name,
            "pages": len(document.pages),
            "chunks": sum(c.document_id == document.id for c in self.index.chunks),
            "bytes": len(document.data),
            "uploaded_at": document.created_at,
            "url": f"/api/documents/{document.id}/file",
        }

    def list_documents(self):
        with self.lock:
            return [self._metadata(d) for d in self.documents]

    def add(self, filename: str, data: bytes):
        document = extract_document(filename, data, self.settings)
        with self.lock:
            existing = next((d for d in self.documents if d.sha256 == document.sha256), None)
            if existing:
                return {**self._metadata(existing), "duplicate": True}
            if len(self.documents) >= self.settings.max_documents:
                raise DocumentError(
                    f"This demo supports at most {self.settings.max_documents} documents."
                )
            updated = self.documents + [document]
            index = self._build(updated)
            self.store.insert(document)
            self.documents, self.index = updated, index
            return {**self._metadata(document), "duplicate": False}

    def get(self, document_id: str) -> Document:
        with self.lock:
            document = next((d for d in self.documents if d.id == document_id), None)
            if document is None:
                raise KeyError(document_id)
            return document

    def delete(self, document_id: str):
        with self.lock:
            self.get(document_id)
            updated = [d for d in self.documents if d.id != document_id]
            index = self._build(updated)
            self.store.delete(document_id)
            self.documents, self.index = updated, index

    @staticmethod
    def source(label: str, hit: Hit, quote: str | None = None):
        return {
            "label": label,
            "document_id": hit.chunk.document_id,
            "filename": hit.chunk.filename,
            "page": hit.chunk.page,
            "excerpt": quote or hit.chunk.text,
            "score": round(hit.score, 4),
            "url": f"/api/documents/{hit.chunk.document_id}/file#page={hit.chunk.page}",
        }

    def ask(self, request: Question):
        start = perf_counter()
        question = request.question.strip()
        if len(question) < 3:
            raise ValueError("Please enter a question with at least three characters.")
        with self.lock:
            if request.document_ids is not None:
                known = {d.id for d in self.documents}
                if set(request.document_ids) - known:
                    raise KeyError("One of the selected documents no longer exists.")
            hits = self.index.search(question, request.top_k * 3, request.document_ids)
        # Avoid filling all results with neighboring chunks from one page.
        per_page = Counter()
        selected = []
        for hit in hits:
            key = (hit.chunk.document_id, hit.chunk.page)
            if hit.score >= self.settings.score_threshold and per_page[key] < 2:
                selected.append(hit)
                per_page[key] += 1
            if len(selected) >= request.top_k:
                break
        result = {
            "question": question,
            "status": "not_found",
            "mode": "extractive",
            "answer": "I could not find sufficiently relevant passages in the selected documents.",
            "sources": [],
            "notice": None,
            "retrieval": self.settings.retrieval,
        }
        if selected:
            result.update(
                status="evidence_only",
                answer="These are the most relevant source passages. Read the excerpts to confirm whether they answer your question.",
                sources=[self.source(f"S{i}", h) for i, h in enumerate(selected, 1)],
            )
            if self.generator is not None:
                try:
                    generated = self.generator.generate(question, selected)
                    citations = validate_citations(generated, selected)
                    if generated.insufficient_evidence:
                        result.update(
                            status="not_found",
                            mode="llm",
                            sources=[],
                            answer="The retrieved passages do not establish an answer to this question.",
                        )
                    else:
                        result.update(
                            status="answered",
                            mode="llm",
                            answer=generated.answer,
                            sources=[
                                self.source(label, hit, quote) for label, hit, quote in citations
                            ],
                        )
                except Exception as exc:
                    # Never include provider errors, credentials, document text or prompts in logs.
                    logger.warning("Generated answer unavailable (%s)", type(exc).__name__)
                    result["notice"] = (
                        "Generated answers were unavailable or citations could not be verified. Showing source passages instead."
                    )
        result["latency_ms"] = round((perf_counter() - start) * 1000, 1)
        return result
