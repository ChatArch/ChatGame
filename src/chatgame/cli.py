"""chatgame CLI。"""

from __future__ import annotations

import sys
import click

_GAMES: dict[str, str] = {
    "cow-puzzle": "牛牛摆放谜题",
}


# ── 顶层命令组 ────────────────────────────────────────────────────────────────

@click.group()
@click.version_option(package_name="chatgame")
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
