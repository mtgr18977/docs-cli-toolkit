import sys
import types
import json
import csv
from pathlib import Path

# Stub dependencies before import
fake_numpy = types.ModuleType("numpy")
class FakeArray(list):
    @property
    def size(self):
        return len(self)

fake_numpy.array = lambda x: FakeArray(x)
fake_numpy.dot = lambda a, b: sum(i*j for i,j in zip(a,b))
fake_numpy.linalg = types.SimpleNamespace(norm=lambda v: sum(x*x for x in v) ** 0.5)
sys.modules.setdefault("numpy", fake_numpy)

fake_google = types.ModuleType("google")
fake_genai = types.ModuleType("google.generativeai")
setattr(fake_genai, "embed_content", lambda model=None, content=None: {"embedding": [1.0, 0.0]})
fake_google.generativeai = fake_genai
sys.modules.setdefault("google", fake_google)
sys.modules.setdefault("google.generativeai", fake_genai)
fake_dotenv = types.ModuleType("dotenv")
setattr(fake_dotenv, "load_dotenv", lambda *a, **k: None)
sys.modules.setdefault("dotenv", fake_dotenv)
sys.modules.setdefault("openai", types.ModuleType("openai"))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluate_coverage import get_relevant_chunks, evaluate_coverage


def test_get_relevant_chunks_orders_by_similarity():
    chunks = [
        {"embedding": [1.0, 0.0], "name": "A"},
        {"embedding": [0.5, 0.5], "name": "B"},
        {"embedding": [-1.0, 0.0], "name": "C"},
    ]
    top = get_relevant_chunks([1.0, 0.0], chunks, top_k=2)
    assert len(top) == 2
    assert top[0]["chunk"] == chunks[0]
    assert top[1]["chunk"] == chunks[1]


def test_evaluate_coverage_simple_flow(monkeypatch, tmp_path):
    qa_file = tmp_path / "qa.csv"
    with open(qa_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["question", "response"])
        writer.writeheader()
        writer.writerow({"question": "Q1", "response": "A."})

    chunks_file = tmp_path / "chunks.json"
    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump([
            {
                "document_title": "Doc",
                "chunk_title": "Sec",
                "document_filepath": "d.md",
                "embedding": [1.0, 0.0],
                "chunk_content": "content",
            }
        ], f)

    out_file = tmp_path / "out.json"

    monkeypatch.setattr(
        sys.modules['evaluate_coverage'],
        'generate_embedding_with_retry',
        lambda text, api_key, model=None: [1.0, 0.0],
    )

    result = evaluate_coverage(
        qa_filepath=str(qa_file),
        chunks_filepath=str(chunks_file),
        top_k_chunks=1,
        output_json_path=str(out_file),
        provider="gemini",
        gemini_api_key="KEY",
    )

    assert result is True
    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data[0]["status"].startswith("Encontrada")
