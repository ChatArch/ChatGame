"""chatgame web serve — 启动后端 + 前端服务。"""

from __future__ import annotations

import signal
import socket
import subprocess
import sys
from pathlib import Path

import click

from chatgame.web.node import detect as detect_node, run_npm

_REPO_ROOT = Path(__file__).resolve().parents[3]
_WEB_DIR   = _REPO_ROOT / "web"


def _port_open(port: int) -> bool:
    try:
        with socket.create_connection(("localhost", port), timeout=1):
            return True
    except OSError:
        return False


def status(backend_port: int = 8000, frontend_port: int = 5173) -> None:
    be = _port_open(backend_port)
    fe = _port_open(frontend_port)
    be_label = click.style("running ✓", fg="green") if be else click.style("stopped ✗", fg="red")
    fe_label = click.style("running ✓", fg="green") if fe else click.style("stopped ✗", fg="red")
    click.echo(f"  后端   http://localhost:{backend_port:<5}  {be_label}")
    click.echo(f"  前端   http://localhost:{frontend_port:<5}  {fe_label}")


def serve(
    backend_only: bool = False,
    frontend_only: bool = False,
    backend_port: int = 8000,
    frontend_port: int = 5173,
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

    if not frontend_only:
        click.echo(click.style(f"▶ 后端启动", bold=True) +
                   f"  http://localhost:{backend_port}")
        procs.append(subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "chatgame.api:app", "--reload", f"--port={backend_port}",
        ]))

    if not backend_only:
        if not _WEB_DIR.exists():
            click.echo(click.style("⚠  前端目录 web/ 不存在，跳过", fg="yellow"), err=True)
        else:
            click.echo(click.style(f"▶ 前端启动", bold=True) +
                       f"  http://localhost:{frontend_port}")
            rt = detect_node()
            if rt["source"] == "nvm":
                import shlex
                cmd = (
                    'export NVM_DIR="$HOME/.nvm" && '
                    '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
                    f"cd {shlex.quote(str(_WEB_DIR))} && npm run dev"
                )
                procs.append(subprocess.Popen(["bash", "-c", cmd]))
            else:
                procs.append(subprocess.Popen(
                    ["npm", "run", "dev"], cwd=_WEB_DIR
                ))

    if not procs:
        click.echo("没有服务被启动。", err=True)
        sys.exit(1)

    click.echo("\nCtrl-C 停止所有服务\n")
    for p in procs:
        p.wait()
