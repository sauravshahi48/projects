from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from docassist.api import ROOT, create_app
from docassist.config import Settings
from docassist.generation import LangChainGenerator
from docassist.models import GroundedAnswer, GroundedCitation, Question
from docassist.service import Assistant


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=tmp_path)


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def upload_text(client, name="leave.txt", content=b"Employees receive 18 days of annual leave."):
    return client.post("/api/documents", files=[("files", (name, content))])


def test_empty_library_abstains_and_ui_loads(client):
    assert client.get("/").status_code == 200
    assert "SourceDesk" in client.get("/").text
    assert client.get("/assets/app.js").status_code == 200
    result = client.post(
        "/api/ask", json={"question": "What is the annual leave allowance?"}
    ).json()
    assert result["status"] == "not_found"
    assert result["sources"] == []


def test_pdf_citations_point_to_correct_page_and_original_file(client):
    file = ROOT / "samples" / "Employee_Handbook.pdf"
    response = client.post("/api/documents", files=[("files", (file.name, file.read_bytes()))])
    assert response.json()["errors"] == []
    result = client.post(
        "/api/ask", json={"question": "How many days of annual leave do employees receive?"}
    ).json()
    assert result["mode"] == "extractive"
    assert result["status"] == "evidence_only"
    source = result["sources"][0]
    assert source["page"] == 2
    assert source["filename"] == file.name
    assert "18 days" in source["excerpt"]
    assert source["url"].endswith("#page=2")
    original = client.get(source["url"].split("#")[0])
    assert original.content == file.read_bytes()
    assert original.headers["content-type"] == "application/pdf"


def test_duplicate_contents_are_not_reindexed(client):
    first = upload_text(client).json()["documents"][0]
    second = upload_text(client, name="different-name.txt").json()["documents"][0]
    assert first["duplicate"] is False
    assert second["duplicate"] is True
    assert first["id"] == second["id"]
    assert len(client.get("/api/documents").json()["documents"]) == 1


def test_document_scope_filters_before_returning_results(client):
    first = upload_text(client).json()["documents"][0]
    second = upload_text(
        client, "other.txt", b"Laptop equipment reimbursement is INR 60000."
    ).json()["documents"][0]
    result = client.post(
        "/api/ask", json={"question": "annual leave", "document_ids": [second["id"]]}
    ).json()
    assert result["status"] == "not_found"
    result = client.post(
        "/api/ask", json={"question": "annual leave", "document_ids": [first["id"]]}
    ).json()
    assert all(s["document_id"] == first["id"] for s in result["sources"])
    assert (
        client.post("/api/ask", json={"question": "annual leave", "document_ids": []}).json()[
            "sources"
        ]
        == []
    )


def test_deletion_removes_index_and_persistent_record(client, settings):
    doc = upload_text(client).json()["documents"][0]
    assert client.delete(f"/api/documents/{doc['id']}").status_code == 200
    assert client.get(f"/api/documents/{doc['id']}/file").status_code == 404
    assert client.delete(f"/api/documents/{doc['id']}").status_code == 404
    assert client.post("/api/ask", json={"question": "annual leave"}).json()["sources"] == []
    assert Assistant(settings).list_documents() == []


def test_restart_restores_documents_and_search(settings):
    first = Assistant(settings)
    document = first.add("leave.txt", b"Annual leave allowance is 18 days.")
    second = Assistant(settings)
    result = second.ask(Question(question="annual leave"))
    assert result["sources"][0]["document_id"] == document["id"]


@pytest.mark.parametrize(
    "name,data,message",
    [
        ("empty.txt", b"", "empty"),
        ("script.exe", b"not a document", "Supported"),
        ("broken.pdf", b"not a PDF", "valid PDF"),
        ("bad.txt", b"\xff\xfe\xfd", "UTF-8"),
        ("tiny.txt", b"   ", "No readable text"),
    ],
)
def test_invalid_files_return_clear_errors(client, name, data, message):
    result = upload_text(client, name, data).json()
    assert not result["documents"]
    assert message in result["errors"][0]["error"]


def test_blank_pdf_requests_ocr(client):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    buffer = BytesIO()
    writer.write(buffer)
    result = upload_text(client, "scan.pdf", buffer.getvalue()).json()
    assert "OCR" in result["errors"][0]["error"]


def test_password_protected_pdf_is_rejected(client):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("secret")
    buffer = BytesIO()
    writer.write(buffer)
    result = upload_text(client, "locked.pdf", buffer.getvalue()).json()
    assert "Password-protected" in result["errors"][0]["error"]


def test_filename_is_not_a_storage_path_and_content_is_served_as_text(client):
    doc = upload_text(
        client, "../../<img>.txt", b"<script>alert('x')</script> Annual leave is 18 days."
    ).json()["documents"][0]
    assert doc["name"] == "<img>.txt"
    response = client.get(doc["url"])
    assert response.headers["content-type"].startswith("text/plain")
    assert response.headers["x-content-type-options"] == "nosniff"


def test_unknown_document_filter_and_invalid_question(client):
    assert (
        client.post(
            "/api/ask", json={"question": "annual leave", "document_ids": ["missing"]}
        ).status_code
        == 404
    )
    assert client.post("/api/ask", json={"question": "   "}).status_code == 400
    assert client.post("/api/ask", json={"question": "a"}).status_code == 422
    assert client.post("/api/ask", json={"question": "leave", "top_k": 100}).status_code == 422


def test_file_size_page_and_document_limits(tmp_path):
    settings = Settings(data_dir=tmp_path, max_bytes=100, max_pages=1, max_documents=1)
    with TestClient(create_app(settings)) as client:
        assert "limit" in upload_text(client, "big.txt", b"x" * 101).json()["errors"][0]["error"]
        assert (
            "too large"
            in upload_text(
                client, "pages.txt", b"Annual leave is 18 days.\fTravel costs are covered."
            ).json()["errors"][0]["error"]
        )
        upload_text(client)
        assert (
            "at most 1"
            in upload_text(client, "second.txt", b"The learning budget is INR 12000.").json()[
                "errors"
            ][0]["error"]
        )


def test_demo_is_idempotent(client):
    assert len(client.post("/api/demo").json()["documents"]) == 2
    assert all(d["duplicate"] for d in client.post("/api/demo").json()["documents"])
    assert len(client.get("/api/documents").json()["documents"]) == 2


def test_demo_capacity_is_checked_before_adding_any_samples(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path, max_documents=1))) as client:
        assert client.post("/api/demo").status_code == 400
        assert client.get("/api/documents").json()["documents"] == []


def test_unknown_topic_abstains(client):
    client.post("/api/demo")
    result = client.post(
        "/api/ask", json={"question": "What is the orbital velocity of Neptune?"}
    ).json()
    assert result["status"] == "not_found"
    assert result["sources"] == []


class FakeStructuredModel:
    def __init__(self, result):
        self.result = result
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return self.result


def make_generated_assistant(settings, result):
    model = FakeStructuredModel(result)
    generator = LangChainGenerator(settings, structured_model=model)
    assistant = Assistant(settings, generator=generator)
    assistant.add("leave.txt", b"Employees receive 18 days of annual leave.")
    return assistant, model


def test_generation_uses_context_and_verifies_citations(settings):
    generated = GroundedAnswer(
        answer="Employees receive 18 days of annual leave [S1].",
        insufficient_evidence=False,
        citations=[
            GroundedCitation(source_id="S1", quote="Employees receive 18 days of annual leave.")
        ],
    )
    assistant, model = make_generated_assistant(settings, generated)
    result = assistant.ask(Question(question="annual leave"))
    assert result["status"] == "answered"
    assert result["sources"][0]["label"] == "S1"
    assert "Employees receive 18 days" in model.messages[1][1]
    assert "untrusted" in model.messages[0][1]


@pytest.mark.parametrize(
    "answer,source_id,quote",
    [
        ("Employees receive 99 days [S1].", "S1", "Employees receive 99 days of annual leave."),
        ("Employees receive 18 days [S99].", "S99", "Employees receive 18 days of annual leave."),
        ("Employees receive 18 days.", "S1", "Employees receive 18 days of annual leave."),
        (
            "Employees receive 18 days [S1]. A bonus is guaranteed.",
            "S1",
            "Employees receive 18 days of annual leave.",
        ),
    ],
)
def test_unverifiable_generation_falls_back_to_evidence(settings, answer, source_id, quote):
    generated = GroundedAnswer(
        answer=answer,
        insufficient_evidence=False,
        citations=[GroundedCitation(source_id=source_id, quote=quote)],
    )
    assistant, _ = make_generated_assistant(settings, generated)
    result = assistant.ask(Question(question="annual leave"))
    assert result["mode"] == "extractive"
    assert result["status"] == "evidence_only"
    assert result["notice"]
    assert "99 days" not in result["answer"]


def test_model_can_abstain_on_related_but_unsupported_question(settings):
    generated = GroundedAnswer(answer="Not established.", insufficient_evidence=True, citations=[])
    assistant, _ = make_generated_assistant(settings, generated)
    result = assistant.ask(Question(question="Can annual leave be sold?"))
    assert result["status"] == "not_found"
    assert result["sources"] == []


def test_provider_failure_falls_back_without_leaking_error(settings):
    class FailingGenerator:
        def generate(self, *_):
            raise RuntimeError("private provider error with credentials")

    assistant = Assistant(settings, generator=FailingGenerator())
    assistant.add("leave.txt", b"Employees receive 18 days of annual leave.")
    result = assistant.ask(Question(question="annual leave"))
    assert result["status"] == "evidence_only"
    assert "credentials" not in str(result)


def test_failed_indexing_does_not_persist_partial_upload(settings, monkeypatch):
    assistant = Assistant(settings)
    assistant.add("leave.txt", b"Employees receive 18 days of annual leave.")

    def fail(_):
        raise RuntimeError("index failed")

    monkeypatch.setattr(assistant.retriever, "build", fail)
    with pytest.raises(RuntimeError):
        assistant.add("expenses.txt", b"Laptop reimbursement is INR 60000.")
    assert len(Assistant(settings).list_documents()) == 1
