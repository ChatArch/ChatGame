"""chatgame web serve — 启动安装态或开发态 Web 服务。"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import shlex
from pathlib import Path

import click

from chatgame.web.node import detect as detect_node
from chatgame.web.paths import has_static_assets, package_static_dir, resolve_frontend_dir


def _port_open(port: int) -> bool:
    try:
        with socket.create_connection(("localhost", port), timeout=1):
            return True
    except OSError:
        return False


def _resolved_assets_dir(assets_dir: str | None = None) -> Path | None:
    candidates: list[Path] = []
    if assets_dir:
        candidates.append(Path(assets_dir).expanduser().resolve())
    candidates.append(package_static_dir())

    for candidate in candidates:
        if has_static_assets(candidate):
            return candidate
    return None


def _spawn_backend(
    backend_port: int,
    assets_dir: Path | None = None,
    with_reload: bool = False,
    disable_ui: bool = False,
) -> subprocess.Popen:
    env = os.environ.copy()
    if assets_dir:
        env["CHATGAME_WEB_ASSETS_DIR"] = str(assets_dir)
    if disable_ui:
        env["CHATGAME_DISABLE_WEB_UI"] = "1"

    args = [
        sys.executable,
        "-m",
        "uvicorn",
        "chatgame.api:app",
        f"--port={backend_port}",
    ]
    if with_reload:
        args.append("--reload")
    return subprocess.Popen(args, env=env)


def _spawn_static_server(assets_dir: Path, frontend_port: int) -> subprocess.Popen:
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "http.server",
            str(frontend_port),
            "--directory",
            str(assets_dir),
        ]
    )


def _spawn_vite_process(frontend_dir: Path, frontend_port: int, backend_port: int) -> subprocess.Popen:
    env = os.environ.copy()
    env["CHATGAME_FRONTEND_PORT"] = str(frontend_port)
    env["CHATGAME_BACKEND_PORT"] = str(backend_port)
    runtime = detect_node()
    if runtime["source"] == "nvm":
        cmd = (
            'export NVM_DIR="$HOME/.nvm" && '
            '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
            f'export CHATGAME_FRONTEND_PORT={shlex.quote(str(frontend_port))} && '
            f'export CHATGAME_BACKEND_PORT={shlex.quote(str(backend_port))} && '
            f"cd {shlex.quote(str(frontend_dir))} && "
            f"npm run dev -- --port {shlex.quote(str(frontend_port))}"
        )
        return subprocess.Popen(["bash", "-c", cmd], env=env)
    return subprocess.Popen(["npm", "run", "dev", "--", "--port", str(frontend_port)], cwd=frontend_dir, env=env)


def status(backend_port: int = 8000, frontend_port: int = 5173, dev: bool = False) -> None:
    be = _port_open(backend_port)
    be_label = click.style("running ✓", fg="green") if be else click.style("stopped ✗", fg="red")
    click.echo(f"  Web/API http://localhost:{backend_port:<5}  {be_label}")
    if dev:
        fe = _port_open(frontend_port)
        fe_label = click.style("running ✓", fg="green") if fe else click.style("stopped ✗", fg="red")
        click.echo(f"  Vite   http://localhost:{frontend_port:<5}  {fe_label}")


def serve(
    backend_only: bool = False,
    frontend_only: bool = False,
    backend_port: int = 8000,
    frontend_port: int = 5173,
    dev: bool = False,
    frontend_dir: str | None = None,
    assets_dir: str | None = None,
) -> None:
    procs: list[subprocess.Popen] = []

    def _stop(sig, frame):
        click.echo("\n停止所有服务…")
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        sys.exit(0)

    signal.signal(signal.SIGINT,  _stop)
    signal.signal(signal.SIGTERM, _stop)

    if backend_only and frontend_only:
        raise click.ClickException("--backend-only 与 --frontend-only 不能同时使用")

    if dev:
        source_dir = resolve_frontend_dir(frontend_dir=frontend_dir)
        if not frontend_only:
            click.echo(click.style("▶ 后端启动", bold=True) + f"  http://localhost:{backend_port}")
            procs.append(_spawn_backend(backend_port=backend_port, with_reload=True, disable_ui=backend_only))
        if not backend_only:
            click.echo(click.style("▶ 前端启动", bold=True) + f"  http://localhost:{frontend_port}")
            procs.append(_spawn_vite_process(source_dir, frontend_port, backend_port))
    else:
        resolved_assets = _resolved_assets_dir(assets_dir)
        if frontend_only:
            if not resolved_assets:
                raise click.ClickException("未找到可服务的静态资源，请使用 --assets-dir 指定目录，或先执行 chatgame web build")
            click.echo(click.style("▶ 静态前端启动", bold=True) + f"  http://localhost:{frontend_port}")
            procs.append(_spawn_static_server(resolved_assets, frontend_port))
        else:
            if assets_dir and not resolved_assets:
                raise click.ClickException(f"静态资源目录不可用：{assets_dir}")
            if resolved_assets:
                click.echo(click.style("▶ Web/API 启动", bold=True) + f"  http://localhost:{backend_port}")
                click.echo(f"  静态资源目录：{resolved_assets}")
            else:
                click.echo(click.style("▶ API 启动", bold=True) + f"  http://localhost:{backend_port}")
                click.echo("  未找到静态资源目录，仅提供 API")
            procs.append(
                _spawn_backend(
                    backend_port=backend_port,
                    assets_dir=None if backend_only else resolved_assets,
                    with_reload=False,
                    disable_ui=backend_only,
                )
            )

    if not procs:
        click.echo("没有服务被启动。", err=True)
        sys.exit(1)

    click.echo("\nCtrl-C 停止所有服务\n")
    for p in procs:
        p.wait()
