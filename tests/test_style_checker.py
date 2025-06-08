import json
from pathlib import Path
import types
import sys

fake_numpy = types.ModuleType("numpy")
fake_numpy.array = lambda x: x
fake_numpy.dot = lambda a, b: sum(i * j for i, j in zip(a, b))
fake_numpy.linalg = types.SimpleNamespace(norm=lambda v: sum(x * x for x in v) ** 0.5)
sys.modules.setdefault("numpy", fake_numpy)
fake_google = types.ModuleType("google")
fake_genai = types.ModuleType("google.generativeai")
setattr(fake_genai, "embed_content", lambda model=None, content=None: {"embedding": [1.0, 0.0]})
fake_google.generativeai = fake_genai
sys.modules.setdefault("google", fake_google)
sys.modules.setdefault("google.generativeai", fake_genai)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import style_checker


def test_cosine_similarity_basic():
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert style_checker.cosine_similarity(a, b) == 0.0


def test_check_style_flags_sentence(monkeypatch, tmp_path):
    emb_file = tmp_path / "emb.json"
    with open(emb_file, "w", encoding="utf-8") as f:
        json.dump([{"text": "ok", "embedding": [1.0, 0.0]}], f)

    def fake_embed(text, api_key, model=None):
        if "bad" in text:
            return [0.0, 1.0]
        return [1.0, 0.0]

    monkeypatch.setattr(style_checker, "generate_embedding_with_retry", fake_embed)

    text = "good sentence. bad style."
    issues = style_checker.check_style(text, str(emb_file), api_key="X", threshold=0.8)
    assert len(issues) == 1
    assert issues[0]["sentence"] == "bad style"
