from click.testing import CliRunner

from chatgame.cli import main


def test_web_setup_interactive_invokes_runner(mocker):
    run_setup = mocker.patch("chatgame.web.setup.run_setup", return_value=True)

    result = CliRunner().invoke(main, ["web", "setup", "-i", "--frontend-dir", "/tmp/frontend"])

    assert result.exit_code == 0
    run_setup.assert_called_once_with(install_frontend=True, frontend_dir="/tmp/frontend")


def test_web_build_invokes_builder(mocker):
    build = mocker.patch("chatgame.web.build.build")

    result = CliRunner().invoke(
        main,
        ["web", "build", "--frontend-dir", "/tmp/frontend", "--dist-dir", "/tmp/dist", "--clean"],
    )

    assert result.exit_code == 0
    build.assert_called_once_with(frontend_dir="/tmp/frontend", dist_dir="/tmp/dist", clean=True)


def test_web_serve_invokes_runtime(mocker):
    serve = mocker.patch("chatgame.web.serve.serve")

    result = CliRunner().invoke(
        main,
        [
            "web",
            "serve",
            "--dev",
            "--frontend-dir",
            "/tmp/frontend",
            "--assets-dir",
            "/tmp/dist",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--frontend-port",
            "5174",
        ],
    )

    assert result.exit_code == 0
    serve.assert_called_once_with(
        backend_only=False,
        frontend_only=False,
        backend_port=9000,
        frontend_port=5174,
        host="0.0.0.0",
        dev=True,
        frontend_dir="/tmp/frontend",
        assets_dir="/tmp/dist",
    )


def test_web_status_invokes_runtime(mocker):
    status = mocker.patch("chatgame.web.serve.status")

    result = CliRunner().invoke(
        main,
        ["web", "status", "--host", "0.0.0.0", "--port", "8123", "--frontend-port", "5175", "--dev"],
    )

    assert result.exit_code == 0
    status.assert_called_once_with(backend_port=8123, frontend_port=5175, dev=True, host="0.0.0.0")
