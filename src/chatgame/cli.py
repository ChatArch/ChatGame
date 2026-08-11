"""chatgame CLI。"""

from __future__ import annotations

import sys
import click

from chatgame import __version__

_GAMES: dict[str, str] = {
    "cow-puzzle": "牛牛摆放谜题",
}


def _short_help(command: click.Command) -> str:
    help_text = (command.short_help or command.help or "").strip()
    if not help_text:
        return ""
    return help_text.splitlines()[0].strip()


def _format_argument(argument: click.Argument) -> str:
    metavar = (argument.metavar or argument.name or "ARG").upper().replace("_", "-")
    if argument.nargs != 1:
        metavar = f"{metavar}..."
    if argument.required:
        return metavar
    return f"[{metavar}]"


def _format_option(option: click.Option) -> str:
    visible = [flag for flag in option.opts if flag.startswith("--")]
    visible.extend(flag for flag in option.opts if flag not in visible)
    if not visible:
        return ""
    flag = visible[0]
    if option.is_flag or option.flag_value is not None:
        return f"[{flag}]"
    metavar = (option.metavar or option.name or "VALUE").upper().replace("_", "-")
    return f"[{flag} {metavar}]"


def _format_signature(command: click.Command) -> str:
    parts: list[str] = []
    for param in command.params:
        if getattr(param, "hidden", False):
            continue
        if isinstance(param, click.Argument):
            parts.append(_format_argument(param))
        elif isinstance(param, click.Option):
            if param.name in {"help", "version", "tree"}:
                continue
            item = _format_option(param)
            if item:
                parts.append(item)
    return " " + " ".join(parts) if parts else ""


def _click_group_children(command: click.Command) -> list[tuple[str, click.Command]]:
    if not isinstance(command, click.Group):
        return []
    ctx = click.Context(command, info_name=command.name)
    children: list[tuple[str, click.Command]] = []
    for name in command.list_commands(ctx):
        child = command.get_command(ctx, name)
        if child is not None:
            children.append((name, child))
    return children


def _tree_command_line(command: click.Command, path: str) -> str:
    line = f"{path}{_format_signature(command)}"
    help_text = _short_help(command)
    if help_text:
        line = f"{line} # {help_text}"
    return line


def _render_click_command(command: click.Command, path: str, prefix: str = "", is_last: bool = True) -> list[str]:
    connector = "└── " if is_last else "├── "
    lines = [f"{prefix}{connector}{_tree_command_line(command, path)}"]
    children = [(name, child) for name, child in _click_group_children(command) if child]
    child_prefix = prefix + ("    " if is_last else "│   ")
    for index, (name, child) in enumerate(children):
        lines.extend(
            _render_click_command(
                child,
                f"{path} {name}",
                prefix=child_prefix,
                is_last=index == len(children) - 1,
            )
        )
    return lines


def render_cli_tree(command: click.Command) -> str:
    """Render the real registered Click command tree."""

    root_name = command.name or "chatgame"
    lines = [_tree_command_line(command, root_name)]
    root_entries = [
        ("--help", "Show this message and exit."),
        ("--version", "Show the version and exit."),
        ("--tree", "Print the registered command tree."),
    ]
    children = _click_group_children(command)
    total_entries = len(root_entries) + len(children)
    entry_index = 0
    for option, help_text in root_entries:
        entry_index += 1
        connector = "└── " if entry_index == total_entries else "├── "
        lines.append(f"{connector}{option} # {help_text}")
    for name, child in children:
        entry_index += 1
        lines.extend(
            _render_click_command(
                child,
                name,
                is_last=entry_index == total_entries,
            )
        )
    return "\n".join(lines)


def _print_cli_tree(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return None
    click.echo(render_cli_tree(ctx.command))
    ctx.exit()


# ── 顶层命令组 ────────────────────────────────────────────────────────────────

@click.group(name="chatgame")
@click.version_option(version=__version__, prog_name="chatgame")
@click.option(
    "--tree",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_print_cli_tree,
    help="Print the registered command tree.",
)
def main() -> None:
    """chatgame — 游戏谜题求解工具。"""


# ── solve ─────────────────────────────────────────────────────────────────────

@main.command()
@click.argument("image", type=click.Path(exists=True))
@click.option("-g", "--game", default="cow-puzzle", show_default=True,
              help=f"游戏类型（{' / '.join(_GAMES)}）")
@click.option("-n", "--size", default=None, type=int,
              help="棋盘边长（默认自动推断）")
@click.option("-o", "--output", default=None, type=click.Path(),
              help="标注结果图保存路径")
@click.option("-v", "--verbose", is_flag=True,
              help="打印颜色矩阵等调试信息")
def solve(image: str, game: str, size: int | None, output: str | None, verbose: bool) -> None:
    """从游戏截图解析并求解谜题。"""
    if game not in _GAMES:
        raise click.BadParameter(
            f"未知游戏 {game!r}，可用：{', '.join(_GAMES)}",
            param_hint="'-g / --game'",
        )
    from chatgame.games.cow_puzzle.__main__ import run as cow_puzzle_run

    cow_puzzle_run(image, n=size, output=output, verbose=verbose)


# ── games ─────────────────────────────────────────────────────────────────────

@main.command(name="games")
def list_games() -> None:
    """列出已支持的游戏。"""
    click.echo("已支持游戏：")
    for gid, desc in _GAMES.items():
        click.echo(f"  {gid:<16} {desc}")


# ── web ───────────────────────────────────────────────────────────────────────

@main.group()
def web() -> None:
    """Web 服务管理（后端 + 前端）。"""


@web.command()
def setup() -> None:
    """检查 Web 运行环境。"""
    from chatgame.web.setup import run_setup
    ok = run_setup()
    if not ok:
        sys.exit(1)


@web.command()
@click.option("--host",          default="127.0.0.1", show_default=True,
              help="服务监听地址；局域网/IP 访问可设为 0.0.0.0")
@click.option("--port",          default=8000, show_default=True, help="后端端口")
@click.option("--reload",        is_flag=True, help="启用 uvicorn 热重载（适用于开发调试）")
def serve(
    host: str,
    port: int,
    reload: bool,
) -> None:
    """启动 Web 服务。"""
    from chatgame.web.serve import serve as _serve
    _serve(
        backend_port=port,
        host=host,
        reload=reload,
    )


if __name__ == "__main__":
    main()
