import sys
import types
from pathlib import Path

# Stub dependencies before import
fake_google = types.ModuleType("google")
fake_genai = types.ModuleType("google.generativeai")
setattr(fake_genai, "embed_content", lambda model=None, content=None: {"embedding": [0.1, 0.2]})
fake_google.generativeai = fake_genai
sys.modules.setdefault("google", fake_google)
sys.modules.setdefault("google.generativeai", fake_genai)
sys.modules.setdefault("openai", types.ModuleType("openai"))
fake_dotenv = types.ModuleType("dotenv")
setattr(fake_dotenv, "load_dotenv", lambda *a, **k: None)
sys.modules.setdefault("dotenv", fake_dotenv)
sys.modules.setdefault("requests", types.ModuleType("requests"))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generate_embeddings import split_content_into_semantic_chunks


def test_split_content_into_semantic_chunks_basic():
    content = (
        "## Metadata_Start\n"
        "## title: Test Doc\n"
        "## slug: test-doc\n"
        "## Metadata_End\n"
        "\n"
        "## Section One\n"
        "Paragraph one.\n"
        "## Section Two\n"
        "Paragraph two.\n"
    )
    chunks = split_content_into_semantic_chunks(content, "Test Doc", "file.md", "test-doc")
    assert len(chunks) == 2
    assert chunks[0]["chunk_title"] == "Section One"
    assert chunks[0]["document_slug"] == "test-doc"
    assert "Paragraph one" in chunks[0]["chunk_content"]
    assert chunks[1]["chunk_title"] == "Section Two"
