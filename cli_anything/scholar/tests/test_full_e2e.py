"""端到端测试 — 调用真实 OpenAlex API（需要网络）"""

import json
import subprocess

import pytest

from cli_anything.scholar.core.openalex import (
    get_author,
    get_author_works,
    get_related_works,
    search_authors,
    tag_text,
)


@pytest.mark.e2e
class TestOpenAlexAPI:
    def test_search_authors_returns_results(self):
        results = search_authors("Albert Einstein", per_page=3)
        assert len(results) > 0

    def test_search_author_has_required_fields(self):
        results = search_authors("Yoshua Bengio", per_page=1)
        assert len(results) > 0
        a = results[0]
        assert a.openalex_id
        assert a.display_name
        assert a.works_count > 0

    def test_get_author_by_orcid(self):
        author = get_author("0000-0001-6187-6610")  # Yoshua Bengio
        assert author is not None
        assert author.works_count > 0

    def test_get_author_by_openalex_id(self):
        author = get_author("A5003442464")  # Yoshua Bengio
        assert author is not None
        assert author.display_name

    def test_get_author_works(self):
        author = get_author("0000-0001-6187-6610")
        assert author is not None
        works = get_author_works(author.openalex_id, per_page=5)
        assert len(works) > 0
        assert all(w.title for w in works)

    def test_tag_text_returns_topics(self):
        result = tag_text("Deep learning for natural language processing")
        assert len(result.topics) > 0
        assert len(result.keywords) > 0
        assert result.topics[0].display_name

    def test_tag_text_with_abstract(self):
        result = tag_text(
            "Attention is All You Need",
            abstract="We propose a new simple network architecture, the Transformer.",
        )
        assert len(result.topics) > 0


@pytest.mark.e2e
class TestCLIBinary:
    def test_help(self):
        r = subprocess.run(["cli-anything-scholar", "--help"], capture_output=True, text=True)
        assert r.returncode == 0
        assert "scholar" in r.stdout.lower()

    def test_search_json_output(self):
        r = subprocess.run(
            ["cli-anything-scholar", "--json", "scholar", "search", "Einstein", "-n", "2"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert isinstance(data, list)
        assert len(data) > 0
        assert "display_name" in data[0]

    def test_tag_json_output(self):
        r = subprocess.run(
            ["cli-anything-scholar", "--json", "scholar", "tag", "Deep learning"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert "topics" in data
        assert "keywords" in data
