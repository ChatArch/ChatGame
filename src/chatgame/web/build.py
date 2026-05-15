"""chatgame web build。"""

from __future__ import annotations

import shutil
from pathlib import Path

import click

from chatgame.web.node import run_npm
from chatgame.web.paths import default_build_dir, resolve_frontend_dir


def build(
    frontend_dir: str | None = None,
    dist_dir: str | None = None,
    clean: bool = False,
) -> Path:
    """构建前端静态资源并返回输出目录。"""
    source_dir = resolve_frontend_dir(frontend_dir=frontend_dir)
    output_dir = Path(dist_dir).expanduser().resolve() if dist_dir else default_build_dir()

    if clean and output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.parent.mkdir(parents=True, exist_ok=True)

    click.echo(f"前端源码目录：{source_dir}")
    click.echo(f"构建输出目录：{output_dir}")

    result = run_npm(
        ["run", "build", "--", "--outDir", str(output_dir)],
        cwd=source_dir,
    )
    if result.returncode != 0:
        raise click.ClickException(result.stderr or result.stdout or "前端构建失败")

    click.echo(click.style("✓ 前端构建完成", fg="green"))
    return output_dir
