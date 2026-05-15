from pathlib import Path

import pytest

from chatgame.web.paths import default_build_dir, has_static_assets, resolve_frontend_dir


def test_default_build_dir_uses_cwd(tmp_path):
    assert default_build_dir(tmp_path) == tmp_path / ".chatgame" / "web-dist"


def test_resolve_frontend_dir_prefers_web_subdir(tmp_path):
    web_dir = tmp_path / "web"
    web_dir.mkdir()
    (web_dir / "package.json").write_text("{}", encoding="utf-8")

    assert resolve_frontend_dir(cwd=tmp_path) == web_dir


def test_resolve_frontend_dir_uses_explicit_dir(tmp_path):
    frontend_dir = tmp_path / "frontend-app"
    frontend_dir.mkdir()
    (frontend_dir / "package.json").write_text("{}", encoding="utf-8")

    assert resolve_frontend_dir(frontend_dir=frontend_dir, cwd=tmp_path) == frontend_dir


def test_resolve_frontend_dir_raises_when_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        resolve_frontend_dir(cwd=tmp_path)


def test_has_static_assets_requires_index_html(tmp_path):
    assets_dir = tmp_path / "dist"
    assets_dir.mkdir()
    assert not has_static_assets(assets_dir)

    (assets_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    assert has_static_assets(assets_dir)
