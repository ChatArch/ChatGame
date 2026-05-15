"""Node.js 检测工具（参考 chattool setup nodejs 的检测逻辑）。"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


MIN_NODE_MAJOR = 18


def _run_bash(cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)


def _cmd_out(args: list[str]) -> str:
    r = subprocess.run(args, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def _bash_out(cmd: str) -> str:
    r = _run_bash(cmd)
    return r.stdout.strip() if r.returncode == 0 else ""


def _parse_major(version: str) -> int | None:
    v = version.lstrip("v").split(".", 1)[0]
    return int(v) if v.isdigit() else None


def _detect_from_path() -> dict:
    node = shutil.which("node")
    npm  = shutil.which("npm")
    nv   = _cmd_out(["node", "-v"]) if node else ""
    mv   = _cmd_out(["npm",  "-v"]) if npm  else ""
    return {"node": node, "npm": npm, "node_ver": nv, "npm_ver": mv,
            "major": _parse_major(nv), "source": "path"}


def _detect_from_nvm() -> dict:
    nvm_sh = Path.home() / ".nvm" / "nvm.sh"
    if not nvm_sh.exists():
        return {"node": "", "npm": "", "node_ver": "", "npm_ver": "",
                "major": None, "source": "nvm"}
    pfx = 'export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
    node = _bash_out(pfx + "command -v node")
    npm  = _bash_out(pfx + "command -v npm")
    nv   = _bash_out(pfx + "node -v") if node else ""
    mv   = _bash_out(pfx + "npm -v")  if npm  else ""
    return {"node": node, "npm": npm, "node_ver": nv, "npm_ver": mv,
            "major": _parse_major(nv), "source": "nvm"}


def detect() -> dict:
    """返回可用的 Node.js 运行时信息字典。优先 nvm（版本更高时）。"""
    p = _detect_from_path()
    n = _detect_from_nvm()
    score = lambda r: (r["major"] or 0) + (1 if r["node"] else 0) + (1 if r["npm"] else 0)
    return n if score(n) > score(p) else p


def is_ok(rt: dict | None = None) -> bool:
    rt = rt or detect()
    return bool(rt["node"] and rt["npm"] and rt["major"] and rt["major"] >= MIN_NODE_MAJOR)


def run_npm(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """运行 npm 命令，兼容 nvm 环境。"""
    rt = detect()
    if rt["source"] == "nvm":
        import shlex
        cwd_part = f"cd {shlex.quote(str(cwd))} && " if cwd else ""
        cmd = (
            'export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
            f"{cwd_part}npm {' '.join(shlex.quote(a) for a in args)}"
        )
        return _run_bash(cmd)
    return subprocess.run(["npm", *args], cwd=cwd, capture_output=True, text=True)
