"""Optional real LangChain/SDK serialization test; all HTTP is mocked locally."""

import json

import pytest

from docassist.config import Settings
from docassist.models import Question
from docassist.service import Assistant


def test_real_langchain_structured_adapter_with_mock_http(tmp_path, monkeypatch):
    langchain_openai = pytest.importorskip("langchain_openai")
    # Support SDK releases using either HTTPX generation without sending a network request.
    base_client = pytest.importorskip("openai._base_client")
    http = getattr(base_client, "httpx2", None) or getattr(base_client, "httpx")
    real_chat_model = langchain_openai.ChatOpenAI
    requests = []

    def respond(request):
        requests.append(json.loads(request.content))
        content = {
            "answer": "Employees receive 18 days of annual leave [S1].",
            "insufficient_evidence": False,
            "citations": [
                {"source_id": "S1", "quote": "Employees receive 18 days of annual leave."}
            ],
        }
        return http.Response(
            200,
            json={
                "id": "chatcmpl-local-test",
                "object": "chat.completion",
                "created": 1,
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": json.dumps(content)},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            },
        )

    transport = http.MockTransport(respond)
    with http.Client(transport=transport, trust_env=False) as client:
        async_client = http.AsyncClient(transport=transport, trust_env=False)

        def local_chat_model(**kwargs):
            return real_chat_model(**kwargs, http_client=client, http_async_client=async_client)

        monkeypatch.setattr(langchain_openai, "ChatOpenAI", local_chat_model)
        settings = Settings(
            data_dir=tmp_path, llm="openai", api_key="test-key", llm_model="test-model"
        )
        assistant = Assistant(settings)
        assistant.add("leave.txt", b"Employees receive 18 days of annual leave.")
        result = assistant.ask(Question(question="annual leave"))
        assert result["status"] == "answered", result
        assert result["sources"][0]["label"] == "S1"
        assert requests[0]["response_format"]["type"] == "json_schema"
        assert "sources" in requests[0]["messages"][1]["content"]
        import asyncio

        asyncio.run(async_client.aclose())
