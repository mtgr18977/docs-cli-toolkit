import sys
from pathlib import Path
import types

# Ensure project root is on sys.path for imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Provide a minimal pandas stub so limpa_csv imports without the real library
sys.modules.setdefault("pandas", types.ModuleType("pandas"))

from limpa_csv import clean_text


def test_clean_text_removes_extra_spaces():
    assert clean_text("  Hello   world!  ") == "Hello world!"


def test_clean_text_removes_special_characters():
    assert clean_text("Hello#$% World@@!") == "Hello World!"


def test_clean_text_combination():
    assert clean_text("  Python@@  rocks!!!$$  ") == "Python rocks!!!"
