from types import SimpleNamespace

import click
import pytest

from chatgame.web.build import build


def test_build_outputs_to_requested_dir(tmp_path, mocker):
    frontend_dir = tmp_path / "web"
    frontend_dir.mkdir()
    (frontend_dir / "package.json").write_text("{}", encoding="utf-8")
    run_npm = mocker.patch("chatgame.web.build.run_npm", return_value=SimpleNamespace(returncode=0, stderr="", stdout=""))

    dist_dir = tmp_path / "dist"
    output = build(frontend_dir=str(frontend_dir), dist_dir=str(dist_dir))

    assert output == dist_dir
    run_npm.assert_called_once()
    args, kwargs = run_npm.call_args
    assert args[0][:3] == ["run", "build", "--"]
    assert kwargs["cwd"] == frontend_dir


def test_build_clean_removes_previous_output(tmp_path, mocker):
    frontend_dir = tmp_path / "web"
    frontend_dir.mkdir()
    (frontend_dir / "package.json").write_text("{}", encoding="utf-8")
    mocker.patch("chatgame.web.build.run_npm", return_value=SimpleNamespace(returncode=0, stderr="", stdout=""))

    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    old_file = dist_dir / "stale.txt"
    old_file.write_text("old", encoding="utf-8")

    build(frontend_dir=str(frontend_dir), dist_dir=str(dist_dir), clean=True)

    assert not old_file.exists()


def test_build_raises_click_exception_on_failure(tmp_path, mocker):
    frontend_dir = tmp_path / "web"
    frontend_dir.mkdir()
    (frontend_dir / "package.json").write_text("{}", encoding="utf-8")
    mocker.patch(
        "chatgame.web.build.run_npm",
        return_value=SimpleNamespace(returncode=1, stderr="npm failed", stdout=""),
    )

    with pytest.raises(click.ClickException, match="npm failed"):
        build(frontend_dir=str(frontend_dir), dist_dir=str(tmp_path / "dist"))


def test_build_raises_friendly_error_when_frontend_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(click.ClickException, match="开发者命令"):
        build(frontend_dir=None, dist_dir=str(tmp_path / "dist"))
