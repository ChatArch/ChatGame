"""chatgame web setup — 环境检查与安装。"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from chatgame.web.node import MIN_NODE_MAJOR, detect as detect_node, is_ok as node_ok, run_npm

# chatgame 根目录（src/chatgame/web/setup.py → 上三级）
_REPO_ROOT = Path(__file__).resolve().parents[3]
_WEB_DIR   = _REPO_ROOT / "web"


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

def check_frontend(install: bool = False) -> bool:
    _head("前端依赖")

    if not _WEB_DIR.exists():
        _fail(f"前端目录不存在：{_WEB_DIR}")
        return False

    node_modules = _WEB_DIR / "node_modules"
    if node_modules.exists():
        _ok("node_modules 已安装")
        return True

    if install:
        _info("正在运行 npm install …")
        r = run_npm(["install", "--registry", "https://registry.npmmirror.com"],
                    cwd=_WEB_DIR)
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

def run_setup(install_frontend: bool = False) -> bool:
    """执行全量环境检查，返回是否全部通过。"""
    py_ok   = check_python()
    nd_ok   = check_node()
    fe_ok   = check_frontend(install=install_frontend)

    click.echo()
    if py_ok and nd_ok and fe_ok:
        click.echo(click.style("✓ 环境就绪，可运行：chatgame web serve", fg="green", bold=True))
        return True
    else:
        click.echo(click.style("⚠  存在未满足的依赖，请根据上方提示处理", fg="yellow", bold=True))
        return False
