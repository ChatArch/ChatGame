from pathlib import Path

from chatgame.web import setup as web_setup


def test_setup_succeeds_with_packaged_assets_without_frontend_source(tmp_path, mocker):
    assets_dir = tmp_path / "web_static"
    assets_dir.mkdir()
    (assets_dir / "index.html").write_text("<html></html>", encoding="utf-8")

    mocker.patch("chatgame.web.setup.check_python", return_value=True)
    check_node = mocker.patch("chatgame.web.setup.check_node", return_value=True)
    mocker.patch("chatgame.web.setup.package_static_dir", return_value=assets_dir)

    assert web_setup.run_setup(install_frontend=False, frontend_dir=None) is True
    check_node.assert_called_once_with(required=False)


def test_setup_fails_when_packaged_assets_missing_and_no_source(mocker, tmp_path):
    assets_dir = tmp_path / "web_static"
    assets_dir.mkdir()

    mocker.patch("chatgame.web.setup.check_python", return_value=True)
    mocker.patch("chatgame.web.setup.check_node", return_value=True)
    mocker.patch("chatgame.web.setup.package_static_dir", return_value=assets_dir)

    assert web_setup.run_setup(install_frontend=False, frontend_dir=None) is False


def test_setup_requires_node_when_frontend_source_requested(mocker):
    mocker.patch("chatgame.web.setup.check_python", return_value=True)
    check_node = mocker.patch("chatgame.web.setup.check_node", return_value=True)
    mocker.patch("chatgame.web.setup.check_frontend", return_value=True)

    assert web_setup.run_setup(install_frontend=True, frontend_dir="/tmp/web") is True
    check_node.assert_called_once_with(required=True)
