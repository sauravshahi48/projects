"""Inspectable lexical baseline, with optional local embeddings + FAISS hybrid search."""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from .models import Chunk, Hit


class Retriever:
    def __init__(self, backend: str, model_name: str):
        self.backend = backend
        self.model_name = model_name
        self.encoder = None
        if backend == "hybrid":
            try:
                import faiss  # noqa: F401
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    'Install semantic dependencies: pip install -e ".[semantic]"'
                ) from exc
            self.encoder = SentenceTransformer(model_name, device="cpu")

    def build(self, chunks: list[Chunk]):
        # Construct completely before publishing: failed indexing leaves the old index usable.
        return SearchIndex(chunks, self.encoder)


class SearchIndex:
    def __init__(self, chunks: list[Chunk], encoder=None):
        self.chunks = tuple(chunks)
        self.encoder = encoder
        self.vectorizer = None
        self.matrix = None
        self.vectors = None
        self.faiss_index = None
        if not chunks:
            return
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
            max_features=60_000,
        )
        try:
            self.matrix = vectorizer.fit_transform([c.text for c in chunks])
            self.vectorizer = vectorizer
        except ValueError as exc:
            if "empty vocabulary" not in str(exc):
                raise
        if encoder is not None:
            import faiss

            self.vectors = np.asarray(
                encoder.encode(
                    [c.text for c in chunks], normalize_embeddings=True, show_progress_bar=False
                ),
                dtype="float32",
            )
            self.faiss_index = faiss.IndexFlatIP(self.vectors.shape[1])
            self.faiss_index.add(self.vectors)

    def search(self, query: str, top_k: int, document_ids: list[str] | None = None) -> list[Hit]:
        if not self.chunks or document_ids == []:
            return []
        lexical = np.zeros(len(self.chunks), dtype="float32")
        if self.vectorizer is not None:
            lexical = linear_kernel(self.vectorizer.transform([query]), self.matrix).ravel()
        scores = lexical
        if self.faiss_index is not None:
            vector = np.asarray(
                self.encoder.encode([query], normalize_embeddings=True, show_progress_bar=False),
                dtype="float32",
            )
            distances, indices = self.faiss_index.search(vector, len(self.chunks))
            semantic = np.zeros(len(self.chunks), dtype="float32")
            semantic[indices[0]] = np.clip(distances[0], 0, 1)
            scores = 0.55 * semantic + 0.45 * lexical
        allowed = set(document_ids) if document_ids is not None else None
        order = np.argsort(-scores, kind="stable")
        hits = []
        for i in order:
            chunk = self.chunks[int(i)]
            if allowed is not None and chunk.document_id not in allowed:
                continue
            if scores[i] <= 0:
                continue
            hits.append(Hit(chunk=chunk, score=float(scores[i])))
            if len(hits) == top_k:
                break
        return hits
