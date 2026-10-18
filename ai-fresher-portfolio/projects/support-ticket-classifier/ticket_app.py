import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from ticket_model import TicketModel

ROOT = Path(__file__).parent


class TicketRequest(BaseModel):
    text: str = Field(min_length=10, max_length=2000)


class Review(BaseModel):
    category: Literal["account", "billing", "orders", "technical"]


def create_app(data_dir: Path | None = None):
    model = TicketModel()
    folder = Path(data_dir) if data_dir else ROOT / ".data"
    folder.mkdir(parents=True, exist_ok=True)
    db_path = folder / "tickets.sqlite3"
    with sqlite3.connect(db_path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS tickets
            (id TEXT PRIMARY KEY, created_at TEXT, text TEXT, suggested_category TEXT,
             probability REAL, requires_review INTEGER, reviewed_category TEXT)""")
    app = FastAPI(title="Support Ticket Triage", version="1.0.0")

    @app.get("/")
    def home():
        return FileResponse(ROOT / "static" / "index.html")

    @app.get("/api/metrics")
    def metrics():
        return model.report

    @app.post("/api/classify")
    def classify(request: TicketRequest):
        text = request.text.strip()
        if len(text) < 10:
            raise HTTPException(400, "Enter at least ten non-whitespace characters.")
        prediction = model.predict(text)
        ticket_id = uuid.uuid4().hex
        with sqlite3.connect(db_path) as db:
            db.execute(
                "INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    ticket_id,
                    datetime.now(UTC).isoformat(),
                    text,
                    prediction["suggested_category"],
                    prediction["model_probability"],
                    int(prediction["requires_review"]),
                    None,
                ),
            )
        return {"id": ticket_id, **prediction}

    @app.get("/api/tickets")
    def recent():
        with sqlite3.connect(db_path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM tickets ORDER BY created_at DESC LIMIT 20").fetchall()
        return {"tickets": [dict(r) for r in rows]}

    @app.post("/api/tickets/{ticket_id}/review")
    def review(ticket_id: str, request: Review):
        with sqlite3.connect(db_path) as db:
            cursor = db.execute(
                "UPDATE tickets SET reviewed_category = ? WHERE id = ?",
                (request.category, ticket_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(404, "Ticket not found.")
        return {
            "id": ticket_id,
            "reviewed_category": request.category,
            "notice": "Review saved locally. The model was not retrained automatically.",
        }

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("ticket_app:create_app", factory=True, host="127.0.0.1", port=8001)
