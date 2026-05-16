from click.testing import CliRunner

from chatgame.cli import main


def test_web_setup_invokes_runner(mocker):
    run_setup = mocker.patch("chatgame.web.setup.run_setup", return_value=True)

    result = CliRunner().invoke(main, ["web", "setup"])

    assert result.exit_code == 0
    run_setup.assert_called_once_with()


def test_web_serve_invokes_runtime(mocker):
    serve = mocker.patch("chatgame.web.serve.serve")

    result = CliRunner().invoke(
        main,
        [
            "web",
            "serve",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
        ],
    )

    assert result.exit_code == 0
    serve.assert_called_once_with(
        backend_port=9000,
        host="0.0.0.0",
        reload=False,
    )
