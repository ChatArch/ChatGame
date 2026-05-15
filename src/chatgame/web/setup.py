"""chatgame web setup — 安装态 Web 运行环境检查。"""

from __future__ import annotations

import click

from chatgame.web.paths import has_static_assets, package_static_dir


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


# ── 前端依赖检查 ──────────────────────────────────────────────────────────────

def check_frontend() -> bool:
    _head("Web 静态资源")
    packaged_assets = package_static_dir()

    if has_static_assets(packaged_assets):
        _ok(f"包内静态资源已就绪：{packaged_assets}")
        _info("可直接运行：chatgame web serve")
        return True

    _fail("未找到包内静态资源；当前安装不可直接运行 Web UI，请重新安装或等待修复后的发布版本。")
    return False


# ── 主入口 ────────────────────────────────────────────────────────────────────

def run_setup() -> bool:
    """执行安装态 Web 运行检查，返回是否全部通过。"""
    py_ok = check_python(required_solver=False)
    fe_ok = check_frontend()

    click.echo()
    if py_ok and fe_ok:
        click.echo(click.style("✓ 环境就绪，可运行：chatgame web serve", fg="green", bold=True))
        return True

    click.echo(click.style("⚠  存在未满足的依赖，请根据上方提示处理", fg="yellow", bold=True))
    return False
