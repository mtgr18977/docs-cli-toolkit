from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from merge_markdown import consolidate_markdown_files


def test_consolidate_markdown_files(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "a.md").write_text("# A", encoding="utf-8")
    sub = docs_dir / "sub"
    sub.mkdir()
    (sub / "b.md").write_text("# B", encoding="utf-8")

    output = tmp_path / "out.md"
    consolidate_markdown_files(str(docs_dir), str(output))
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "# A" in text and "# B" in text
