"""chatgame CLI。"""

from __future__ import annotations

import sys
import click

from chatgame.games.cow_puzzle.__main__ import run as cow_puzzle_run

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
@click.option("-i", "--interactive", "interactive", flag_value=True,  default=None,
              help="交互模式：自动安装缺失的前端依赖")
@click.option("-I", "--no-interactive", "interactive", flag_value=False,
              help="非交互模式：只检查，不安装")
@click.option("--frontend-dir", type=click.Path(path_type=str), default=None,
              help="前端源码目录；默认从当前目录推断")
def setup(interactive: bool | None, frontend_dir: str | None) -> None:
    """检查并安装所有依赖（Python 环境 + Node.js + 前端包）。"""
    from chatgame.web.setup import run_setup
    install_frontend = interactive is True
    ok = run_setup(install_frontend=install_frontend, frontend_dir=frontend_dir)
    if not ok:
        sys.exit(1)


@web.command()
@click.option("--backend-only",  is_flag=True, help="仅启动后端")
@click.option("--frontend-only", is_flag=True, help="仅启动前端")
@click.option("--port",          default=8000, show_default=True, help="后端端口")
@click.option("--frontend-port", default=5173, show_default=True, help="前端端口")
@click.option("--dev", is_flag=True, help="开发模式：启动 Vite dev server")
@click.option("--frontend-dir", type=click.Path(path_type=str), default=None,
              help="前端源码目录（开发模式或构建时使用）")
@click.option("--assets-dir", type=click.Path(path_type=str), default=None,
              help="已构建静态资源目录（安装态或预构建目录）")
def serve(
    backend_only: bool,
    frontend_only: bool,
    port: int,
    frontend_port: int,
    dev: bool,
    frontend_dir: str | None,
    assets_dir: str | None,
) -> None:
    """启动 Web 服务。默认服务静态资源；加 --dev 启动前后端开发服务。"""
    from chatgame.web.serve import serve as _serve
    _serve(
        backend_only=backend_only,
        frontend_only=frontend_only,
        backend_port=port,
        frontend_port=frontend_port,
        dev=dev,
        frontend_dir=frontend_dir,
        assets_dir=assets_dir,
    )


@web.command()
@click.option("--frontend-dir", type=click.Path(path_type=str), default=None,
              help="前端源码目录；默认从当前目录推断")
@click.option("--dist-dir", type=click.Path(path_type=str), default=None,
              help="前端构建输出目录；默认 ./.chatgame/web-dist/")
@click.option("--clean", is_flag=True, help="构建前清空输出目录")
def build(frontend_dir: str | None, dist_dir: str | None, clean: bool) -> None:
    """构建前端静态资源到指定目录。"""
    from chatgame.web.build import build as _build
    _build(frontend_dir=frontend_dir, dist_dir=dist_dir, clean=clean)


@web.command()
@click.option("--port",          default=8000, show_default=True, help="后端端口")
@click.option("--frontend-port", default=5173, show_default=True, help="前端端口")
@click.option("--dev", is_flag=True, help="按开发模式检查前后端两个端口")
def status(port: int, frontend_port: int, dev: bool) -> None:
    """检查各服务运行状态。"""
    from chatgame.web.serve import status as _status
    _status(backend_port=port, frontend_port=frontend_port, dev=dev)


if __name__ == "__main__":
    main()
