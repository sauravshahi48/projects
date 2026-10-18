"""One process serves the API and the interface. No frontend build step is needed."""

import hashlib
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from .config import Settings
from .ingest import DocumentError
from .models import Question
from .service import Assistant

ROOT = Path(__file__).parent


def create_app(settings: Settings | None = None, assistant: Assistant | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    assistant = assistant or Assistant(settings)
    app = FastAPI(title="SourceDesk Document Assistant", version="1.0.0")
    app.state.assistant = assistant

    @app.middleware("http")
    async def local_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(ROOT / "static" / "index.html")

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "retrieval": settings.retrieval,
            "answer_mode": "llm" if assistant.generator else "extractive",
            "sends_passages_to_provider": assistant.generator is not None,
            "documents": len(assistant.list_documents()),
            "max_file_mb": settings.max_bytes // (1024 * 1024),
            "max_pages": settings.max_pages,
            "max_documents": settings.max_documents,
        }

    @app.get("/api/documents")
    def documents():
        return {"documents": assistant.list_documents()}

    @app.post("/api/documents")
    async def upload(files: list[UploadFile] = File(...)):
        if len(files) > 10:
            for file in files:
                await file.close()
            raise HTTPException(400, "Upload at most 10 files at once.")
        results, errors = [], []
        for file in files:
            try:
                data = await file.read(settings.max_bytes + 1)
                result = await run_in_threadpool(assistant.add, file.filename or "", data)
                results.append(result)
            except DocumentError as exc:
                errors.append({"filename": file.filename or "Unnamed file", "error": str(exc)})
            finally:
                await file.close()
        return {"documents": results, "errors": errors}

    @app.post("/api/demo")
    def demo():
        samples = [(p.name, p.read_bytes()) for p in sorted((ROOT / "samples").glob("*.pdf"))]
        if not samples:
            raise HTTPException(503, "The sample PDFs are missing from this installation.")
        with assistant.lock:
            known = {d.sha256 for d in assistant.documents}
            missing = {hashlib.sha256(data).hexdigest() for _, data in samples} - known
            if len(assistant.documents) + len(missing) > settings.max_documents:
                raise HTTPException(400, "Remove some documents before loading the sample PDFs.")
            try:
                return {"documents": [assistant.add(name, data) for name, data in samples]}
            except DocumentError as exc:
                raise HTTPException(400, str(exc)) from None

    @app.delete("/api/documents/{document_id}")
    def delete(document_id: str):
        try:
            assistant.delete(document_id)
        except KeyError:
            raise HTTPException(404, "Document not found.") from None
        return {"deleted": document_id}

    @app.get("/api/documents/{document_id}/file")
    def document_file(document_id: str):
        try:
            document = assistant.get(document_id)
        except KeyError:
            raise HTTPException(404, "Document not found.") from None
        return Response(
            document.data, media_type=document.mime_type, headers={"Content-Disposition": "inline"}
        )

    @app.post("/api/ask")
    def ask(request: Question):
        try:
            return assistant.ask(request)
        except KeyError as exc:
            raise HTTPException(404, str(exc.args[0])) from None
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None

    app.mount("/assets", StaticFiles(directory=ROOT / "static"), name="assets")
    return app
