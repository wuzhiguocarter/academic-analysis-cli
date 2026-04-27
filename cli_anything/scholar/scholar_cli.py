"""学术搜索 CLI 命令"""

from __future__ import annotations

import dataclasses
import json
import sys

import click

from .core.openalex import (
    DEFAULT_EMAIL,
    get_author,
    get_author_stats,
    get_author_works,
    get_related_works,
    search_authors,
    tag_text,
)
from .utils.output import is_json_mode, print_table, set_json_mode


def _to_dict(obj) -> dict:
    return dataclasses.asdict(obj) if dataclasses.is_dataclass(obj) else obj


def _dump(obj) -> str:
    return json.dumps(_to_dict(obj), ensure_ascii=False, indent=2)


def _dump_list(lst) -> str:
    return json.dumps([_to_dict(o) for o in lst], ensure_ascii=False, indent=2)


@click.group()
@click.option("--json", "json_mode", is_flag=True, help="JSON 格式输出")
def cli(json_mode: bool) -> None:
    """学术搜索工具 — 学者与论文检索（OpenAlex）"""
    if json_mode:
        set_json_mode(True)


@cli.group()
def scholar() -> None:
    """学者与论文检索（OpenAlex）"""


@scholar.command("search")
@click.argument("name")
@click.option("-n", "--limit", default=10, show_default=True, help="最大返回数量")
@click.option("--email", default=DEFAULT_EMAIL, help="OpenAlex polite pool 邮箱")
def scholar_search(name: str, limit: int, email: str) -> None:
    """按姓名搜索学者，返回 ORCID 和机构信息"""
    try:
        authors = search_authors(name, limit, email)
        if is_json_mode():
            click.echo(_dump_list(authors))
            return
        if not authors:
            click.echo("未找到相关学者。")
            return
        rows = [
            {
                "#": i + 1,
                "name": a.display_name,
                "orcid": a.orcid or "—",
                "works": a.works_count,
                "citations": a.cited_by_count,
                "affiliation": ", ".join(a.institutions) or "—",
            }
            for i, a in enumerate(authors)
        ]
        print_table(rows, [
            {"key": "#", "label": "#", "width": 3},
            {"key": "name", "label": "姓名", "width": 20},
            {"key": "orcid", "label": "ORCID", "width": 20},
            {"key": "works", "label": "论文数", "width": 6},
            {"key": "citations", "label": "被引", "width": 8},
            {"key": "affiliation", "label": "机构", "width": 35},
        ])
        click.echo(f"\n共 {len(authors)} 条结果。使用 --json 获取机器可读输出。")
        click.echo("提示：复制 ORCID 并运行 `scholar works <orcid>`")
    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@scholar.command("profile")
@click.argument("orcid_or_id")
@click.option("--stats", is_flag=True, help="显示逐年发表统计")
@click.option("--email", default=DEFAULT_EMAIL, help="OpenAlex polite pool 邮箱")
def scholar_profile(orcid_or_id: str, stats: bool, email: str) -> None:
    """查看学者详情（支持 ORCID 或 OpenAlex ID）"""
    try:
        author = get_author(orcid_or_id, email)
        if not author:
            click.echo(f"未找到学者: {orcid_or_id}", err=True)
            sys.exit(1)
        timeline = get_author_stats(author.openalex_id, email) if stats else None
        if is_json_mode():
            out = dataclasses.asdict(author)
            if timeline:
                out["yearly_works"] = timeline
            click.echo(json.dumps(out, ensure_ascii=False, indent=2))
            return
        click.echo(f"OpenAlex ID:  {author.openalex_id}")
        click.echo(f"姓名:         {author.display_name}")
        click.echo(f"ORCID:        {author.orcid or '—'}")
        click.echo(f"论文数:       {author.works_count}")
        click.echo(f"被引次数:     {author.cited_by_count:,}")
        if author.institutions:
            click.echo(f"机构:         {', '.join(author.institutions)}")
        if timeline:
            click.echo("\n逐年发表量：")
            for year, count in list(timeline.items())[-10:]:
                bar = "█" * min(count, 40)
                click.echo(f"  {year}  {bar} {count}")
    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@scholar.command("works")
@click.argument("orcid_or_id")
@click.option("-n", "--limit", default=25, show_default=True, help="最大获取数量")
@click.option(
    "--sort", default="citations", show_default=True,
    type=click.Choice(["citations", "date"]), help="排序方式",
)
@click.option("--xpac", is_flag=True, help="包含 XPAC 扩展数据集（+1.9亿论文）")
@click.option("--email", default=DEFAULT_EMAIL, help="OpenAlex polite pool 邮箱")
def scholar_works(orcid_or_id: str, limit: int, sort: str, xpac: bool, email: str) -> None:
    """获取学者发表的论文列表"""
    try:
        author = get_author(orcid_or_id, email)
        if not author:
            click.echo(f"未找到学者: {orcid_or_id}", err=True)
            sys.exit(1)
        sort_param = "publication_date:desc" if sort == "date" else "cited_by_count:desc"
        works = get_author_works(author.openalex_id, limit, sort_param, xpac, email)
        if is_json_mode():
            click.echo(_dump_list(works))
            return
        click.echo(f"学者: {author.display_name}  |  总论文数: {author.works_count:,}\n")
        rows = [
            {
                "#": i + 1,
                "year": w.year or "—",
                "title": w.title,
                "type": w.type or "—",
                "cited": w.cited_by_count,
                "oa": "OA" if w.is_open_access else "",
            }
            for i, w in enumerate(works)
        ]
        print_table(rows, [
            {"key": "#", "label": "#", "width": 3},
            {"key": "year", "label": "年份", "width": 4},
            {"key": "title", "label": "标题", "width": 50},
            {"key": "type", "label": "类型", "width": 12},
            {"key": "cited", "label": "被引", "width": 6},
            {"key": "oa", "label": "OA", "width": 2},
        ])
    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@scholar.command("related")
@click.argument("doi_or_id")
@click.option("--email", default=DEFAULT_EMAIL, help="OpenAlex polite pool 邮箱")
def scholar_related(doi_or_id: str, email: str) -> None:
    """查找相关论文（支持 DOI 或 OpenAlex Work ID）"""
    try:
        related = get_related_works(doi_or_id, email)
        if is_json_mode():
            click.echo(_dump_list(related))
            return
        if not related:
            click.echo("未找到相关论文。")
            return
        rows = [
            {
                "#": i + 1,
                "year": w.year or "—",
                "title": w.title,
                "type": w.type or "—",
                "cited": w.cited_by_count,
                "oa": "OA" if w.is_open_access else "",
            }
            for i, w in enumerate(related)
        ]
        print_table(rows, [
            {"key": "#", "label": "#", "width": 3},
            {"key": "year", "label": "年份", "width": 4},
            {"key": "title", "label": "标题", "width": 50},
            {"key": "type", "label": "类型", "width": 12},
            {"key": "cited", "label": "被引", "width": 6},
            {"key": "oa", "label": "OA", "width": 2},
        ])
    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@scholar.command("tag")
@click.argument("title")
@click.option("--abstract", default="", help="摘要文本，提升分类准确度")
@click.option("--email", default=DEFAULT_EMAIL, help="OpenAlex polite pool 邮箱")
def scholar_tag(title: str, abstract: str, email: str) -> None:
    """语义主题标注：输入标题+摘要，获取研究领域和关键词"""
    try:
        result = tag_text(title, abstract, email)
        if is_json_mode():
            click.echo(_dump(result))
            return
        click.echo("主题标签：")
        rows = [
            {
                "topic": t.display_name,
                "field": t.field or "—",
                "domain": t.domain or "—",
                "score": f"{t.score:.3f}" if t.score is not None else "—",
            }
            for t in result.topics
        ]
        print_table(rows, [
            {"key": "topic", "label": "主题", "width": 30},
            {"key": "field", "label": "领域", "width": 20},
            {"key": "domain", "label": "大类", "width": 20},
            {"key": "score", "label": "得分", "width": 6},
        ])
        if result.keywords:
            click.echo(f"\n关键词: {', '.join(result.keywords)}")
    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)
