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
def setup() -> None:
    """检查并安装所有依赖（Python 环境 + Node.js + 前端包）。"""
    import shutil, subprocess

    ok = True

    # Python 包
    click.echo("── Python ──")
    try:
        import chatgame
        click.echo(f"  chatgame    ✓  {chatgame.__version__}")
    except ImportError:
        click.echo("  chatgame    ✗  未安装", err=True)
        ok = False

    for pkg in ("PIL", "sklearn", "numpy", "uvicorn"):
        try:
            __import__(pkg)
            click.echo(f"  {pkg:<12}✓")
        except ImportError:
            click.echo(f"  {pkg:<12}✗  缺失")
            ok = False

    # Node.js
    click.echo("── Node.js ──")
    node = shutil.which("node")
    npm = shutil.which("npm")
    if node:
        ver = subprocess.check_output(["node", "--version"], text=True).strip()
        click.echo(f"  node        ✓  {ver}")
    else:
        click.echo("  node        ✗  未找到，请安装 Node.js >= 18", err=True)
        ok = False
    if npm:
        ver = subprocess.check_output(["npm", "--version"], text=True).strip()
        click.echo(f"  npm         ✓  {ver}")
    else:
        click.echo("  npm         ✗  未找到", err=True)
        ok = False

    click.echo()
    if ok:
        click.echo("✓ 环境就绪")
    else:
        click.echo("⚠  部分依赖缺失，请补齐后重试")
        sys.exit(1)


@web.command()
@click.option("--backend-only", is_flag=True, help="仅启动后端")
@click.option("--frontend-only", is_flag=True, help="仅启动前端")
@click.option("--port", default=8000, show_default=True, help="后端端口")
@click.option("--frontend-port", default=5173, show_default=True, help="前端端口")
def serve(backend_only: bool, frontend_only: bool, port: int, frontend_port: int) -> None:
    """启动 Web 服务（后端 FastAPI + 前端 React）。"""
    import subprocess, signal, os
    from pathlib import Path

    procs: list[subprocess.Popen] = []

    def _stop(sig, frame):
        click.echo("\n停止服务...")
        for p in procs:
            p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    if not frontend_only:
        click.echo(f"▶ 启动后端  http://localhost:{port}")
        procs.append(subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "chatgame.api:app", "--reload", f"--port={port}",
        ]))

    if not backend_only:
        # 前端目录（web/ 下，待创建）
        web_dir = Path(__file__).resolve().parents[3] / "web"
        if not web_dir.exists():
            click.echo("⚠  前端目录 web/ 尚未创建，跳过前端启动", err=True)
        else:
            click.echo(f"▶ 启动前端  http://localhost:{frontend_port}")
            procs.append(subprocess.Popen(["npm", "run", "dev"], cwd=web_dir))

    if not procs:
        click.echo("没有服务被启动。", err=True)
        sys.exit(1)

    click.echo("Ctrl-C 停止所有服务\n")
    for p in procs:
        p.wait()


@web.command()
@click.option("--port", default=8000, show_default=True, help="后端端口")
@click.option("--frontend-port", default=5173, show_default=True, help="前端端口")
def status(port: int, frontend_port: int) -> None:
    """检查各服务运行状态。"""
    import socket

    def _check(host: str, p: int) -> bool:
        try:
            with socket.create_connection((host, p), timeout=1):
                return True
        except OSError:
            return False

    be = _check("localhost", port)
    fe = _check("localhost", frontend_port)

    click.echo(f"  后端  localhost:{port:<6}  {'running ✓' if be else 'stopped ✗'}")
    click.echo(f"  前端  localhost:{frontend_port:<6}  {'running ✓' if fe else 'stopped ✗'}")


if __name__ == "__main__":
    main()
