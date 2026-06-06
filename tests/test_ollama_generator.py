import json

from src.ollama_generator import ollama_generate


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps({"response": "Test answer"}).encode("utf-8")


def test_ollama_generate_posts_expected_payload(monkeypatch):
    captured = {}

    def fake_urlopen(http_request, timeout):
        captured["url"] = http_request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(http_request.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr("src.ollama_generator.request.urlopen", fake_urlopen)

    answer = ollama_generate(
        "Explain accessibility.",
        model="llama3.1:8b",
        base_url="http://localhost:11434",
        temperature=0.2,
        timeout=10,
    )

    assert answer == "Test answer"
    assert captured["url"] == "http://localhost:11434/api/generate"
    assert captured["timeout"] == 10
    assert captured["payload"]["model"] == "llama3.1:8b"
    assert captured["payload"]["prompt"] == "Explain accessibility."
    assert captured["payload"]["stream"] is False
    assert captured["payload"]["options"]["temperature"] == 0.2
