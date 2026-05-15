from chatgame.web import serve as web_serve


def test_spawn_backend_passes_host_to_uvicorn(mocker):
    popen = mocker.patch("subprocess.Popen")

    web_serve._spawn_backend(backend_port=8123, host="0.0.0.0")

    args = popen.call_args.args[0]
    assert "--host=0.0.0.0" in args
    assert "--port=8123" in args


def test_resolved_assets_dir_prefers_env_override(mocker, tmp_path):
    env_assets = tmp_path / "env-assets"
    env_assets.mkdir()
    (env_assets / "index.html").write_text("<html></html>", encoding="utf-8")

    pkg_assets = tmp_path / "pkg-assets"
    pkg_assets.mkdir()
    (pkg_assets / "index.html").write_text("<html></html>", encoding="utf-8")

    mocker.patch.dict("os.environ", {"CHATGAME_WEB_ASSETS_DIR": str(env_assets)})
    mocker.patch("chatgame.web.serve.package_static_dir", return_value=pkg_assets)

    assert web_serve._resolved_assets_dir() == env_assets
