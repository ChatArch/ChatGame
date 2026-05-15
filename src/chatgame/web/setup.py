"""chatgame web setup — 环境检查与安装。"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from chatgame.web.node import MIN_NODE_MAJOR, detect as detect_node, is_ok as node_ok, run_npm
from chatgame.web.paths import resolve_frontend_dir


# ── 彩色输出辅助 ──────────────────────────────────────────────────────────────

def _ok(msg: str)   -> None: click.echo(click.style(f"  ✓  {msg}", fg="green"))
def _fail(msg: str) -> None: click.echo(click.style(f"  ✗  {msg}", fg="red"),   err=True)
def _warn(msg: str) -> None: click.echo(click.style(f"  ⚠  {msg}", fg="yellow"))
def _info(msg: str) -> None: click.echo(f"  ·  {msg}")
def _head(msg: str) -> None: click.echo(click.style(f"\n── {msg}", bold=True))


# ── Python 环境检查 ───────────────────────────────────────────────────────────

def check_python() -> bool:
    _head("Python 环境")
    all_ok = True

    # chatgame 包本身
    try:
        import chatgame
        _ok(f"chatgame {chatgame.__version__}")
    except ImportError:
        _fail("chatgame 未安装")
        all_ok = False

    # 核心依赖
    for pkg, import_name in [
        ("Pillow",       "PIL"),
        ("scikit-learn", "sklearn"),
        ("numpy",        "numpy"),
        ("fastapi",      "fastapi"),
        ("uvicorn",      "uvicorn"),
    ]:
        try:
            mod = __import__(import_name)
            ver = getattr(mod, "__version__", "")
            _ok(f"{pkg}{' ' + ver if ver else ''}")
        except ImportError:
            _fail(f"{pkg} 未安装")
            all_ok = False

    return all_ok


# ── Node.js 检查 ──────────────────────────────────────────────────────────────

def check_node() -> bool:
    _head("Node.js 环境")
    rt = detect_node()

    if not rt["node"]:
        _fail(f"node 未找到（需要 >= {MIN_NODE_MAJOR}）")
        _info("请运行：chattool setup nodejs")
        return False

    major = rt["major"]
    if major and major >= MIN_NODE_MAJOR:
        _ok(f"node {rt['node_ver']}  ({rt['source']})")
    else:
        _warn(f"node {rt['node_ver']} 低于要求 {MIN_NODE_MAJOR}，建议升级")
        _info("请运行：chattool setup nodejs")

    if rt["npm"]:
        _ok(f"npm  {rt['npm_ver']}")
    else:
        _fail("npm 未找到")
        return False

    return bool(major and major >= MIN_NODE_MAJOR)


# ── 前端依赖检查 ──────────────────────────────────────────────────────────────

def check_frontend(install: bool = False, frontend_dir: str | None = None) -> bool:
    _head("前端依赖")

    try:
        web_dir = resolve_frontend_dir(frontend_dir=frontend_dir)
    except FileNotFoundError as exc:
        _fail(str(exc))
        return False

    _info(f"前端源码目录：{web_dir}")

    node_modules = web_dir / "node_modules"
    if node_modules.exists():
        _ok("node_modules 已安装")
        return True

    if install:
        _info("正在运行 npm install …")
        r = run_npm(["install", "--registry", "https://registry.npmmirror.com"],
                    cwd=web_dir)
        if r.returncode == 0:
            _ok("npm install 完成")
            return True
        else:
            _fail("npm install 失败")
            click.echo(r.stderr or r.stdout, err=True)
            return False

    _warn("node_modules 不存在，运行 chatgame web setup -i 自动安装")
    return False


# ── 主入口 ────────────────────────────────────────────────────────────────────

def run_setup(install_frontend: bool = False, frontend_dir: str | None = None) -> bool:
    """执行全量环境检查，返回是否全部通过。"""
    py_ok   = check_python()
    nd_ok   = check_node()
    fe_ok   = check_frontend(install=install_frontend, frontend_dir=frontend_dir)

    click.echo()
    if py_ok and nd_ok and fe_ok:
        click.echo(click.style("✓ 环境就绪，可运行：chatgame web serve", fg="green", bold=True))
        return True
    else:
        click.echo(click.style("⚠  存在未满足的依赖，请根据上方提示处理", fg="yellow", bold=True))
        return False
