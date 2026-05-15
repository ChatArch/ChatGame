from pathlib import Path

from chatgame.web import serve as web_serve


def test_spawn_backend_passes_host_to_uvicorn(mocker):
    popen = mocker.patch("subprocess.Popen")

    web_serve._spawn_backend(backend_port=8123, host="0.0.0.0")

    args = popen.call_args.args[0]
    assert "--host=0.0.0.0" in args
    assert "--port=8123" in args


def test_spawn_static_server_binds_host(mocker, tmp_path):
    popen = mocker.patch("subprocess.Popen")

    web_serve._spawn_static_server(tmp_path, frontend_port=5174, host="0.0.0.0")

    args = popen.call_args.args[0]
    assert args[args.index("--bind") + 1] == "0.0.0.0"
    assert str(tmp_path) in args


def test_spawn_vite_passes_host(mocker, tmp_path):
    popen = mocker.patch("subprocess.Popen")
    mocker.patch("chatgame.web.serve.detect_node", return_value={"source": "path"})

    web_serve._spawn_vite_process(Path(tmp_path), frontend_port=5174, backend_port=8123, host="0.0.0.0")

    args = popen.call_args.args[0]
    assert args == ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5174"]
