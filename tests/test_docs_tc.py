import sys
import types
from pathlib import Path

# Ensure project root on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Import module after stubbing subprocess
import subprocess

import docs_tc


def test_run_script_success(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"):
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")
    monkeypatch.setattr(subprocess, "run", fake_run)
    result = docs_tc.run_script(["echo", "hi"])
    assert isinstance(result, subprocess.CompletedProcess)
    assert result.returncode == 0


def test_run_script_failure(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="err")
    monkeypatch.setattr(subprocess, "run", fake_run)
    result = docs_tc.run_script(["bad", "cmd"])
    assert result is None


def test_main_merge_invokes_run_script(monkeypatch, tmp_path):
    called = {}
    def fake_run_script(cmd, verbose=False):
        called["cmd"] = cmd
        return True
    monkeypatch.setattr(docs_tc, "run_script", fake_run_script)
    # Redirect config file to temp directory to avoid writing to real home
    monkeypatch.setattr(docs_tc, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(docs_tc, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(sys, "argv", ["docs_tc.py", "merge", "docsdir", "out.md"])
    docs_tc.main()
    assert called["cmd"] == ["docs-tc-merge-markdown", "docsdir", "out.md"]


def test_main_style_check_invokes_run_script(monkeypatch, tmp_path):
    called = {}
    def fake_run_script(cmd, verbose=False):
        called["cmd"] = cmd
        return True
    monkeypatch.setattr(docs_tc, "run_script", fake_run_script)
    monkeypatch.setattr(docs_tc, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(docs_tc, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(sys, "argv", [
        "docs_tc.py",
        "style_check",
        "in.txt",
        "style.json",
        "0.9",
        "--api_key",
        "KEY",
    ])
    docs_tc.main()
    assert called["cmd"] == [
        "docs-tc-style-checker",
        "in.txt",
        "style.json",
        "0.9",
        "--api_key",
        "KEY",
    ]


def test_main_full_flow_invokes_all_steps(monkeypatch, tmp_path):
    called = []
    def fake_run_script(cmd, verbose=False):
        called.append(cmd)
        return True
    monkeypatch.setattr(docs_tc, "run_script", fake_run_script)
    monkeypatch.setattr(docs_tc, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(docs_tc, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(sys, "argv", ["docs_tc.py", "full_flow", "docs", "qa.csv"])
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    docs_tc.main()
    expected = [
        ["docs-tc-merge-markdown", "docs", docs_tc.DEFAULT_CORPUS_CONSOLIDATED],
        ["docs-tc-clean-csv", "qa.csv", docs_tc.DEFAULT_QA_PROCESSED],
        ["docs-tc-extract-data", docs_tc.DEFAULT_CORPUS_CONSOLIDATED, docs_tc.DEFAULT_RAW_DOCS],
        ["docs-tc-generate-embeddings", docs_tc.DEFAULT_RAW_DOCS, docs_tc.DEFAULT_EMBEDDINGS, "--provider", "gemini"],
        ["docs-tc-evaluate-coverage", docs_tc.DEFAULT_QA_PROCESSED, docs_tc.DEFAULT_EMBEDDINGS, "-k", "5", "-o", docs_tc.DEFAULT_EVAL_RESULTS],
        ["docs-tc-generate-report-md", docs_tc.DEFAULT_EVAL_RESULTS, docs_tc.DEFAULT_MD_REPORT, "5"],
        ["docs-tc-generate-report-html", docs_tc.DEFAULT_EVAL_RESULTS, docs_tc.DEFAULT_HTML_REPORT, "5"],
    ]
    assert called == expected
