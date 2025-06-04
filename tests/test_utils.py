import sys
import types
from pathlib import Path

# Ensure project root on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Provide minimal stub for google.generativeai so utils imports without dependency
fake_google = types.ModuleType("google")
fake_genai = types.ModuleType("google.generativeai")
setattr(fake_genai, "embed_content", lambda model=None, content=None: {"embedding": [0.1, 0.2]})
fake_google.generativeai = fake_genai
sys.modules.setdefault("google", fake_google)
sys.modules.setdefault("google.generativeai", fake_genai)

from utils import clean_text_for_embedding


def test_clean_text_removes_markdown():
    text = "# Title\n\nThis **bold** and _italic_ text"
    assert clean_text_for_embedding(text) == "Title This bold and italic text"


def test_clean_text_handles_links_and_code():
    md = "See [docs](http://example.com) `code`\n```python\nprint('hi')\n```"
    assert clean_text_for_embedding(md) == "See"

