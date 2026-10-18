import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(".data")
    retrieval: str = "lexical"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm: str = "off"
    llm_model: str = ""
    api_key: str = ""
    min_score: float | None = None
    max_bytes: int = 10 * 1024 * 1024
    max_pages: int = 80
    max_documents: int = 40
    max_characters: int = 600_000
    chunk_size: int = 800
    chunk_overlap: int = 120

    def __post_init__(self):
        if self.retrieval not in {"lexical", "hybrid"}:
            raise ValueError("DOCASSIST_RETRIEVAL must be lexical or hybrid.")
        if self.llm not in {"off", "openai"}:
            raise ValueError("DOCASSIST_LLM must be off or openai.")
        if not 0 <= self.chunk_overlap < self.chunk_size:
            raise ValueError("Chunk overlap must be smaller than chunk size.")
        if self.min_score is not None and not 0 <= self.min_score <= 1:
            raise ValueError("DOCASSIST_MIN_SCORE must be between 0 and 1.")
        if self.llm == "openai" and (not self.api_key or not self.llm_model):
            raise ValueError(
                "Set OPENAI_API_KEY and DOCASSIST_LLM_MODEL to enable generated answers."
            )

    @property
    def score_threshold(self) -> float:
        if self.min_score is not None:
            return self.min_score
        return 0.40 if self.retrieval == "hybrid" else 0.12

    @classmethod
    def from_env(cls):
        from dotenv import load_dotenv

        load_dotenv()
        score = os.getenv("DOCASSIST_MIN_SCORE")
        return cls(
            data_dir=Path(os.getenv("DOCASSIST_DATA_DIR", ".data")).expanduser().resolve(),
            retrieval=os.getenv("DOCASSIST_RETRIEVAL", "lexical"),
            embedding_model=os.getenv(
                "DOCASSIST_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
            ),
            llm=os.getenv("DOCASSIST_LLM", "off"),
            llm_model=os.getenv("DOCASSIST_LLM_MODEL", ""),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            min_score=float(score) if score else None,
        )
