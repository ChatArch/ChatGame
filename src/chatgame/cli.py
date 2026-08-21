"""chatgame CLI。"""

from __future__ import annotations

import sys

import click
from chatstyle import add_tree_option

from chatgame import __version__

_GAMES: dict[str, str] = {
    "cow-puzzle": "牛牛摆放谜题",
}


# ── 顶层命令组 ────────────────────────────────────────────────────────────────

@click.group(
    name="chatgame",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(version=__version__, prog_name="chatgame")
@add_tree_option(renderer_options={"root_name": "chatgame"})
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
    """解析截图并输出求解步骤；--output 写入标注图。"""
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
    """列出已支持的游戏；只读文本输出。"""
    click.echo("已支持游戏：")
    for gid, desc in _GAMES.items():
        click.echo(f"  {gid:<16} {desc}")


# ── web ───────────────────────────────────────────────────────────────────────

@main.group()
def web() -> None:
    """管理安装态 Web 服务（后端 + 前端）。"""


@web.command()
def setup() -> None:
    """检查 Web 运行环境；只读状态输出。"""
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
    """启动长驻 Web 服务；监听指定地址和端口。"""
    from chatgame.web.serve import serve as _serve
    _serve(
        backend_port=port,
        host=host,
        reload=reload,
    )


if __name__ == "__main__":
    main()
