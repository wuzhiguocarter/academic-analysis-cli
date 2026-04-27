"""OpenAlex 公开 API 客户端 — https://docs.openalex.org/"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Optional

BASE = "https://api.openalex.org"
DEFAULT_EMAIL = "wuzhiguocarter@gmail.com"


@dataclass
class AuthorResult:
    openalex_id: str
    display_name: str
    orcid: Optional[str]
    works_count: int
    cited_by_count: int
    institutions: list[str]
    works_api_url: Optional[str]


@dataclass
class WorkResult:
    openalex_id: str
    title: str
    year: Optional[int]
    publication_date: Optional[str]
    type: Optional[str]
    doi: Optional[str]
    journal: Optional[str]
    cited_by_count: int
    is_open_access: bool
    oa_url: Optional[str]
    authors: list[str]
    topics: list[str]


@dataclass
class TopicTag:
    display_name: str
    score: Optional[float]
    field: Optional[str]
    domain: Optional[str]


@dataclass
class TagResult:
    topics: list[TopicTag]
    keywords: list[str]


def _get(path: str, params: dict, email: str = DEFAULT_EMAIL) -> dict:
    clean = {k: str(v) for k, v in params.items() if v is not None and v != ""}
    clean["mailto"] = email
    url = f"{BASE}{path}?{urllib.parse.urlencode(clean)}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"academic-analysis-cli/1.0 (mailto:{email})",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _extract_work(w: dict) -> WorkResult:
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    primary = w.get("primary_location") or {}
    source = primary.get("source") or {}
    oa = w.get("open_access") or {}
    authorships = w.get("authorships") or []
    authors = [
        (a.get("author") or {}).get("display_name", "")
        for a in authorships[:5]
        if (a.get("author") or {}).get("display_name")
    ]
    topics_raw = w.get("topics") or []
    topics = [t.get("display_name", "") for t in topics_raw[:3]]
    return WorkResult(
        openalex_id=w.get("id", ""),
        title=(w.get("title") or "").strip(),
        year=w.get("publication_year"),
        publication_date=w.get("publication_date"),
        type=w.get("type"),
        doi=doi or None,
        journal=source.get("display_name"),
        cited_by_count=w.get("cited_by_count", 0),
        is_open_access=oa.get("is_oa", False),
        oa_url=oa.get("oa_url"),
        authors=authors,
        topics=topics,
    )


def _from_api_author(data: dict) -> AuthorResult:
    affiliations = data.get("affiliations") or []
    institutions = [a.get("display_name", "") for a in affiliations if a.get("display_name")]
    if not institutions:
        last_known = data.get("last_known_institutions") or []
        institutions = [i.get("display_name", "") for i in last_known if i.get("display_name")]
    orcid_raw = data.get("orcid")
    orcid = orcid_raw.replace("https://orcid.org/", "").strip() if orcid_raw else None
    return AuthorResult(
        openalex_id=data.get("id", ""),
        display_name=data.get("display_name", ""),
        orcid=orcid,
        works_count=data.get("works_count", 0),
        cited_by_count=data.get("cited_by_count", 0),
        institutions=institutions[:3],
        works_api_url=data.get("works_api_url"),
    )


def search_authors(name: str, per_page: int = 10, email: str = DEFAULT_EMAIL) -> list[AuthorResult]:
    """按姓名搜索学者"""
    data = _get("/authors", {"search": name, "per-page": min(per_page, 25)}, email)
    return [_from_api_author(r) for r in data.get("results", [])]


def get_author(id_or_orcid: str, email: str = DEFAULT_EMAIL) -> Optional[AuthorResult]:
    """获取单个学者（支持 OpenAlex ID 或 ORCID）"""
    normalized = id_or_orcid.strip()
    if re.match(r"^A\d+$", normalized):
        try:
            data = _get(f"/authors/{normalized}", {}, email)
            return _from_api_author(data)
        except Exception:
            return None
    orcid = normalized.replace("https://orcid.org/", "")
    data = _get("/authors", {"filter": f"orcid:{orcid}", "per-page": 1}, email)
    results = data.get("results", [])
    return _from_api_author(results[0]) if results else None


def get_author_stats(author_id: str, email: str = DEFAULT_EMAIL) -> dict[str, int]:
    """获取学者逐年发表量统计"""
    short = author_id.split("/")[-1]
    data = _get(
        "/works",
        {"filter": f"author.id:{short}", "group_by": "publication_year", "per-page": 1},
        email,
    )
    groups = data.get("group_by", [])
    return {
        str(g["key"]): g["count"]
        for g in sorted(groups, key=lambda g: int(g["key"]) if str(g["key"]).isdigit() else 0)
    }


def get_author_works(
    author_id: str,
    per_page: int = 25,
    sort: str = "cited_by_count:desc",
    include_xpac: bool = False,
    email: str = DEFAULT_EMAIL,
) -> list[WorkResult]:
    """获取学者发表的论文列表"""
    short = author_id.split("/")[-1]
    params: dict = {"filter": f"author.id:{short}", "per-page": min(per_page, 50), "sort": sort}
    if include_xpac:
        params["include_xpac"] = "true"
    data = _get("/works", params, email)
    return [_extract_work(r) for r in data.get("results", [])]


def get_related_works(work_id: str, email: str = DEFAULT_EMAIL) -> list[WorkResult]:
    """查找相关论文（支持 DOI 或 OpenAlex Work ID）"""
    normalized = work_id.strip()
    if normalized.startswith("10."):
        normalized = f"https://doi.org/{normalized}"
    try:
        encoded = urllib.parse.quote(normalized, safe="")
        work_data = _get(f"/works/{encoded}", {"select": "id,related_works"}, email)
        related_ids = work_data.get("related_works", [])
        if not related_ids:
            return []
        ids_short = [r.split("/")[-1] for r in related_ids[:10]]
        filter_str = "|".join(ids_short)
        data = _get("/works", {"filter": f"openalex_id:{filter_str}", "per-page": 10}, email)
        return [_extract_work(r) for r in data.get("results", [])]
    except Exception:
        return []


def tag_text(title: str, abstract: str = "", email: str = DEFAULT_EMAIL) -> TagResult:
    """语义主题标注：输入标题+摘要，返回研究领域和关键词"""
    params: dict = {"title": title}
    if abstract:
        params["abstract"] = abstract
    data = _get("/text", params, email)
    topics = [
        TopicTag(
            display_name=t.get("display_name", ""),
            score=t.get("score"),
            field=(t.get("field") or {}).get("display_name"),
            domain=(t.get("domain") or {}).get("display_name"),
        )
        for t in (data.get("topics") or [])
    ]
    keywords = [k.get("display_name", "") for k in (data.get("keywords") or [])]
    return TagResult(topics=topics, keywords=keywords)
