import builtins
import importlib
import sys

from click.testing import CliRunner
from conftest import IMG_8x8, IMG_10x10
from chatgame.cli import main


def test_top_level_help_command():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "solve" in result.output
    assert "web" in result.output


def test_help_does_not_eager_import_solver(monkeypatch):
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "chatgame.games.cow_puzzle.__main__":
            raise AssertionError("solver imported while rendering help")
        return original_import(name, globals, locals, fromlist, level)

    sys.modules.pop("chatgame.cli", None)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    try:
        cli_module = importlib.import_module("chatgame.cli")
        result = CliRunner().invoke(cli_module.main, ["web", "serve", "--help"])
    finally:
        sys.modules.pop("chatgame.cli", None)
        importlib.import_module("chatgame.cli")

    assert result.exit_code == 0
    assert "启动 Web 服务" in result.output


def test_unknown_command_reports_click_error():
    result = CliRunner().invoke(main, ["serve", "--help"])

    assert result.exit_code != 0
    assert "No such command 'serve'" in result.output


def test_games_command():
    result = CliRunner().invoke(main, ["games"])
    assert result.exit_code == 0
    assert "cow-puzzle" in result.output


def test_solve_unknown_game():
    result = CliRunner().invoke(main, ["solve", str(IMG_8x8), "-g", "unknown-game"])
    assert result.exit_code != 0
    assert "未知游戏" in result.output


def test_solve_8x8(tmp_path):
    result = CliRunner().invoke(main, ["solve", str(IMG_8x8), "-n", "8"])
    assert result.exit_code == 0
    assert "验证通过" in result.output
    assert "第 8 步" in result.output


def test_solve_10x10():
    result = CliRunner().invoke(main, ["solve", str(IMG_10x10), "-n", "10"])
    assert result.exit_code == 0
    assert "验证通过" in result.output
    assert "第 10 步" in result.output


def test_solve_annotate_output(tmp_path):
    out = tmp_path / "solved.png"
    result = CliRunner().invoke(main, ["solve", str(IMG_8x8), "-n", "8", "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert out.stat().st_size > 0
