"""chatgame web serve — 启动安装态 Web 服务。"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path

import click

from chatgame.web.paths import has_static_assets, package_static_dir


def _display_url(host: str, port: int) -> str:
    return f"http://{host}:{port}"


def _resolved_assets_dir() -> Path | None:
    candidates: list[Path] = []
    env_dir = os.getenv("CHATGAME_WEB_ASSETS_DIR")
    if env_dir:
        candidates.append(Path(env_dir).expanduser().resolve())
    candidates.append(package_static_dir())

    for candidate in candidates:
        if has_static_assets(candidate):
            return candidate
    return None


def _spawn_backend(
    backend_port: int,
    host: str = "127.0.0.1",
    assets_dir: Path | None = None,
    reload: bool = False,
) -> subprocess.Popen:
    env = os.environ.copy()
    if assets_dir:
        env["CHATGAME_WEB_ASSETS_DIR"] = str(assets_dir)

    args = [
        sys.executable,
        "-m",
        "uvicorn",
        "chatgame.api:app",
        f"--host={host}",
        f"--port={backend_port}",
    ]
    if reload:
        args.append("--reload")
    return subprocess.Popen(args, env=env)


def serve(
    backend_port: int = 8000,
    host: str = "127.0.0.1",
    reload: bool = False,
) -> None:
    procs: list[subprocess.Popen] = []

    def _stop(sig, frame):
        click.echo("\n停止所有服务…")
        for proc in procs:
            try:
                proc.terminate()
            except Exception:
                pass
        sys.exit(0)

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    resolved_assets = _resolved_assets_dir()
    if resolved_assets:
        click.echo(click.style("▶ Web/API 启动", bold=True) + f"  {_display_url(host, backend_port)}")
        click.echo(f"  静态资源目录：{resolved_assets}")
    else:
        click.echo(click.style("▶ API 启动", bold=True) + f"  {_display_url(host, backend_port)}")
        click.echo("  未找到静态资源目录，仅提供 API")

    procs.append(
        _spawn_backend(
            backend_port=backend_port,
            host=host,
            assets_dir=resolved_assets,
            reload=reload,
        )
    )

    click.echo("\nCtrl-C 停止所有服务\n")
    for proc in procs:
        proc.wait()
