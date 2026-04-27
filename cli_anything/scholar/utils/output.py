"""输出格式化工具"""

from __future__ import annotations

_json_mode = False

BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"


def set_json_mode(enabled: bool) -> None:
    global _json_mode
    _json_mode = enabled


def is_json_mode() -> bool:
    return _json_mode


def _vis_len(s: str) -> int:
    return sum(2 if ord(c) > 0x7F else 1 for c in s)


def _truncate(s: str, max_vis: int) -> str:
    result, vis = [], 0
    for c in s:
        w = 2 if ord(c) > 0x7F else 1
        if vis + w > max_vis:
            result.append("…")
            break
        result.append(c)
        vis += w
    return "".join(result)


def _pad(s: str, width: int) -> str:
    return s + " " * max(0, width - _vis_len(s))


def print_table(rows: list[dict], columns: list[dict]) -> None:
    if not rows:
        print(f"  {DIM}(空){RESET}")
        return

    widths = []
    for col in columns:
        data_max = max(_vis_len(str(r.get(col["key"], ""))) for r in rows)
        widths.append(col.get("width") or max(_vis_len(col["label"]), min(data_max, 40)))

    header = "  ".join(
        f"{BOLD}{_pad(col['label'], widths[i])}{RESET}" for i, col in enumerate(columns)
    )
    print(f"  {header}")
    sep = "──".join("─" * w for w in widths)
    print(f"  {sep}")

    for row in rows:
        line = "  ".join(
            _pad(_truncate(str(row.get(col["key"], "—")), widths[i]), widths[i])
            for i, col in enumerate(columns)
        )
        print(f"  {line}")
