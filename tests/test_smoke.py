"""Smoke test: every module imports and config.toml parses, so CI has something to run before the real tests exist."""

import importlib
import tomllib
from pathlib import Path

import pytest

MODULES = [
    "scraper.fetch",
    "scraper.clean",
    "scraper.discover",
    "rag.chunker",
    "rag.embedder",
    "rag.vector_index",
    "rag.bm25",
    "rag.hybrid",
    "rag.generate",
    "rag.ask",
    "eval.run_eval",
    "api.main",
]

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    importlib.import_module(name)


def test_config_loads():
    with open(ROOT / "config.toml", "rb") as f:
        config = tomllib.load(f)
    assert config["chunking"]["max_tokens"] == 450


def test_urls_txt_has_16_addresses():
    lines = (ROOT / "scraper" / "urls.txt").read_text().split()
    assert len(lines) == 16
