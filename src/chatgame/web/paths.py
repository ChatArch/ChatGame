"""chatgame Web 路径与目录解析。"""

from __future__ import annotations

from pathlib import Path


def package_root() -> Path:
    """返回安装后的 chatgame 包目录。"""
    return Path(__file__).resolve().parents[1]


def package_static_dir() -> Path:
    """返回包内前端静态资源目录。"""
    return package_root() / "web_static"


def default_build_dir(cwd: str | Path | None = None) -> Path:
    """返回默认构建输出目录。"""
    base = Path(cwd or Path.cwd()).resolve()
    return base / ".chatgame" / "web-dist"


def resolve_frontend_dir(frontend_dir: str | Path | None = None, cwd: str | Path | None = None) -> Path:
    """解析前端源码目录。

    查找顺序：
    1. 显式传入的 ``frontend_dir``
    2. ``<cwd>/web``（仓库根目录常见布局）
    3. ``<cwd>``（当前目录本身就是前端目录）
    """
    base = Path(cwd or Path.cwd()).resolve()
    candidates = [Path(frontend_dir).expanduser()] if frontend_dir else [base / "web", base]

    for candidate in candidates:
        path = candidate.resolve()
        if (path / "package.json").exists():
            return path

    searched = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"未找到前端目录，请使用 --frontend-dir 指定。已检查：{searched}")


def has_static_assets(path: str | Path | None) -> bool:
    """目录下是否存在可服务的构建产物。"""
    if not path:
        return False
    root = Path(path).expanduser().resolve()
    return (root / "index.html").exists()
