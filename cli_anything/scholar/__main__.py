"""Entry point — REPL 模式为默认，有参数时单次执行"""

from __future__ import annotations

import shlex
import sys

import click

from .scholar_cli import cli, set_json_mode


def repl() -> None:
    click.echo("学术搜索 REPL — 输入 'help' 查看帮助，'exit' 退出")
    while True:
        try:
            line = input("scholar> ").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo("")
            break
        if not line:
            continue
        if line in ("exit", "quit", "q"):
            break
        try:
            args = shlex.split(line)
        except ValueError as e:
            click.echo(f"输入错误: {e}", err=True)
            continue
        try:
            cli.main(args, standalone_mode=False)
        except click.exceptions.UsageError as e:
            click.echo(f"用法错误: {e}", err=True)
        except SystemExit:
            pass
        except Exception as e:
            click.echo(f"错误: {e}", err=True)


def main() -> None:
    if len(sys.argv) > 1:
        cli()
    else:
        repl()


if __name__ == "__main__":
    main()
