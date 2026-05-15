"""chatgame web setup — 环境检查与安装。"""

from __future__ import annotations

import click

from chatgame.web.node import MIN_NODE_MAJOR, detect as detect_node, run_npm
from chatgame.web.paths import has_static_assets, package_static_dir, resolve_frontend_dir


# ── 彩色输出辅助 ──────────────────────────────────────────────────────────────

def _ok(msg: str)   -> None: click.echo(click.style(f"  ✓  {msg}", fg="green"))
def _fail(msg: str) -> None: click.echo(click.style(f"  ✗  {msg}", fg="red"),   err=True)
def _warn(msg: str) -> None: click.echo(click.style(f"  ⚠  {msg}", fg="yellow"))
def _info(msg: str) -> None: click.echo(f"  ·  {msg}")
def _head(msg: str) -> None: click.echo(click.style(f"\n── {msg}", bold=True))


# ── Python 环境检查 ───────────────────────────────────────────────────────────

def _check_import(pkg: str, import_name: str) -> bool:
    try:
        mod = __import__(import_name)
        ver = getattr(mod, "__version__", "")
        _ok(f"{pkg}{' ' + ver if ver else ''}")
        return True
    except Exception as exc:
        _fail(f"{pkg} 不可用：{exc}")
        return False


def check_python(required_solver: bool = False) -> bool:
    _head("Python 环境")
    all_ok = True

    # chatgame 包本身
    try:
        import chatgame
        _ok(f"chatgame {chatgame.__version__}")
    except ImportError:
        _fail("chatgame 未安装")
        all_ok = False

    # Web 安装态真正必需的依赖
    for pkg, import_name in [
        ("fastapi",      "fastapi"),
        ("uvicorn",      "uvicorn"),
    ]:
        if not _check_import(pkg, import_name):
            all_ok = False

    # 求解器依赖只在显式开发/求解器路径下作为硬要求检查。
    if required_solver:
        _head("求解器依赖")
        for pkg, import_name in [
            ("Pillow",       "PIL"),
            ("numpy",        "numpy"),
            ("scikit-learn", "sklearn"),
        ]:
            if not _check_import(pkg, import_name):
                all_ok = False

    return all_ok


# ── Node.js 检查 ──────────────────────────────────────────────────────────────

def check_node(required: bool = True) -> bool:
    _head("Node.js 环境")
    rt = detect_node()

    if not rt["node"]:
        if required:
            _fail(f"node 未找到（需要 >= {MIN_NODE_MAJOR}）")
            _info("请运行：chattool setup nodejs")
            return False
        _warn(f"node 未找到；安装态运行不需要，但开发前端仍需要 >= {MIN_NODE_MAJOR}")
        return True

    major = rt["major"]
    if major and major >= MIN_NODE_MAJOR:
        _ok(f"node {rt['node_ver']}  ({rt['source']})")
    else:
        level = _warn if not required else _fail
        level(f"node {rt['node_ver']} 低于要求 {MIN_NODE_MAJOR}")
        _info("请运行：chattool setup nodejs")
        if required:
            return False

    if rt["npm"]:
        _ok(f"npm  {rt['npm_ver']}")
    else:
        if required:
            _fail("npm 未找到")
            return False
        _warn("npm 未找到；安装态运行不需要，但开发前端仍需要它")
        return True

    return True if not required else bool(major and major >= MIN_NODE_MAJOR)


# ── 前端依赖检查 ──────────────────────────────────────────────────────────────

def check_frontend(install: bool = False, frontend_dir: str | None = None) -> bool:
    _head("前端依赖")
    packaged_assets = package_static_dir()

    if frontend_dir is None and not install:
        if has_static_assets(packaged_assets):
            _ok(f"包内静态资源已就绪：{packaged_assets}")
            _info("安装态可直接运行：chatgame web serve")
            return True
        _fail(
            "未找到包内静态资源；当前安装态不可直接运行。"
            " 这通常表示发布物缺少前端资源，请重新构建/发布，或在源码仓库中使用 --frontend-dir。"
        )
        return False

    try:
        web_dir = resolve_frontend_dir(frontend_dir=frontend_dir)
    except FileNotFoundError as exc:
        _fail(
            f"{exc} 如需构建或安装前端依赖，请在源码仓库运行，或显式传入 --frontend-dir。"
        )
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
    needs_frontend_source = install_frontend or frontend_dir is not None
    py_ok   = check_python(required_solver=needs_frontend_source)
    nd_ok   = check_node(required=needs_frontend_source)
    fe_ok   = check_frontend(install=install_frontend, frontend_dir=frontend_dir)

    click.echo()
    if py_ok and nd_ok and fe_ok:
        click.echo(click.style("✓ 环境就绪，可运行：chatgame web serve", fg="green", bold=True))
        return True
    else:
        click.echo(click.style("⚠  存在未满足的依赖，请根据上方提示处理", fg="yellow", bold=True))
        return False
