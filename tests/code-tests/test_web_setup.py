from pathlib import Path

from chatgame.web import setup as web_setup


def test_check_python_installed_mode_skips_solver_imports(mocker):
    calls = []

    def fake_check_import(pkg, import_name):
        calls.append((pkg, import_name))
        return True

    mocker.patch("chatgame.web.setup._check_import", side_effect=fake_check_import)

    assert web_setup.check_python(required_solver=False) is True
    assert calls == [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
    ]


def test_check_python_developer_mode_includes_solver_imports(mocker):
    calls = []

    def fake_check_import(pkg, import_name):
        calls.append((pkg, import_name))
        return True

    mocker.patch("chatgame.web.setup._check_import", side_effect=fake_check_import)

    assert web_setup.check_python(required_solver=True) is True
    assert calls == [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("Pillow", "PIL"),
        ("numpy", "numpy"),
        ("scikit-learn", "sklearn"),
    ]


def test_check_import_handles_solver_abi_errors(monkeypatch):
    real_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "sklearn":
            raise AttributeError("_ARRAY_API not found")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", fake_import)

    assert web_setup._check_import("scikit-learn", "sklearn") is False


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
