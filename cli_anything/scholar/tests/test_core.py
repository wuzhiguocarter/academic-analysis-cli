"""单元测试 — 数据转换函数（无网络）"""

from unittest.mock import patch

import pytest

from cli_anything.scholar.core.openalex import (
    TagResult,
    _extract_work,
    _from_api_author,
    get_author,
    search_authors,
    tag_text,
)


class TestExtractWork:
    def test_basic_fields(self):
        raw = {
            "id": "W1234567890",
            "title": "Test Paper",
            "publication_year": 2023,
            "publication_date": "2023-01-01",
            "type": "journal-article",
            "doi": "https://doi.org/10.1234/test",
            "primary_location": {"source": {"display_name": "Nature"}},
            "open_access": {"is_oa": True, "oa_url": "https://example.com"},
            "authorships": [{"author": {"display_name": "John Doe"}}],
            "topics": [{"display_name": "Machine Learning"}],
            "cited_by_count": 42,
        }
        w = _extract_work(raw)
        assert w.openalex_id == "W1234567890"
        assert w.doi == "10.1234/test"
        assert w.journal == "Nature"
        assert w.is_open_access is True
        assert w.authors == ["John Doe"]
        assert w.cited_by_count == 42

    def test_missing_fields_return_defaults(self):
        w = _extract_work({})
        assert w.openalex_id == ""
        assert w.doi is None
        assert w.is_open_access is False
        assert w.authors == []
        assert w.topics == []

    def test_doi_strip(self):
        w = _extract_work({"doi": "https://doi.org/10.5678/abc"})
        assert w.doi == "10.5678/abc"

    def test_authors_capped_at_5(self):
        authorships = [{"author": {"display_name": f"Author{i}"}} for i in range(8)]
        w = _extract_work({"authorships": authorships})
        assert len(w.authors) == 5

    def test_topics_capped_at_3(self):
        topics = [{"display_name": f"Topic{i}"} for i in range(6)]
        w = _extract_work({"topics": topics})
        assert len(w.topics) == 3


class TestFromApiAuthor:
    def test_orcid_strip(self):
        raw = {
            "id": "A1", "display_name": "X", "orcid": "https://orcid.org/0000-0001-2345-6789",
            "works_count": 0, "cited_by_count": 0, "affiliations": [],
        }
        a = _from_api_author(raw)
        assert a.orcid == "0000-0001-2345-6789"

    def test_fallback_to_last_known_institutions(self):
        raw = {
            "id": "A1", "display_name": "X", "orcid": None,
            "works_count": 0, "cited_by_count": 0,
            "affiliations": [],
            "last_known_institutions": [{"display_name": "Stanford"}],
        }
        a = _from_api_author(raw)
        assert a.institutions == ["Stanford"]

    def test_institutions_capped_at_3(self):
        affiliations = [{"display_name": f"Inst{i}"} for i in range(5)]
        raw = {
            "id": "A1", "display_name": "X", "orcid": None,
            "works_count": 0, "cited_by_count": 0, "affiliations": affiliations,
        }
        a = _from_api_author(raw)
        assert len(a.institutions) == 3


class TestSearchAuthors:
    def test_maps_results(self):
        mock = {
            "results": [{
                "id": "A1", "display_name": "Test Author", "orcid": None,
                "works_count": 10, "cited_by_count": 100,
                "affiliations": [], "works_api_url": None,
            }]
        }
        with patch("cli_anything.scholar.core.openalex._get", return_value=mock):
            results = search_authors("Test Author")
        assert len(results) == 1
        assert results[0].display_name == "Test Author"

    def test_empty_results(self):
        with patch("cli_anything.scholar.core.openalex._get", return_value={"results": []}):
            assert search_authors("Nobody") == []


class TestGetAuthor:
    def test_by_openalex_id(self):
        mock = {"id": "A123", "display_name": "Jane", "orcid": None,
                "works_count": 5, "cited_by_count": 50, "affiliations": []}
        with patch("cli_anything.scholar.core.openalex._get", return_value=mock):
            author = get_author("A123")
        assert author is not None
        assert author.display_name == "Jane"

    def test_returns_none_on_error(self):
        with patch("cli_anything.scholar.core.openalex._get", side_effect=Exception("404")):
            assert get_author("A999") is None


class TestTagText:
    def test_basic(self):
        mock = {
            "topics": [{
                "display_name": "Machine Learning", "score": 0.95,
                "field": {"display_name": "CS"}, "domain": {"display_name": "Physical Sciences"},
            }],
            "keywords": [{"display_name": "neural networks"}],
        }
        with patch("cli_anything.scholar.core.openalex._get", return_value=mock):
            result = tag_text("Deep Learning")
        assert isinstance(result, TagResult)
        assert result.topics[0].display_name == "Machine Learning"
        assert result.keywords == ["neural networks"]
