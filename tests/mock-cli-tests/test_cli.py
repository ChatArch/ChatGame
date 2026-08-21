import builtins
import importlib
import sys

from click.testing import CliRunner
from chatstyle import render_click_tree
from conftest import IMG_8x8, IMG_10x10

from chatgame import __version__
from chatgame.cli import main


def test_version_option_reports_package_version():
    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert f"chatgame, version {__version__}" in result.output


def test_top_level_help_command():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "--tree" in result.output
    assert "--tree-brief" in result.output
    assert "solve" in result.output
    assert "games" in result.output
    assert "web" in result.output
    assert "hello" not in result.output.lower()


def test_tree_option_renders_registered_command_surface_without_eager_import(monkeypatch):
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "chatgame.games.cow_puzzle.__main__":
            raise AssertionError("solver imported while rendering tree")
        return original_import(name, globals, locals, fromlist, level)

    sys.modules.pop("chatgame.cli", None)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    try:
        cli_module = importlib.import_module("chatgame.cli")
        result = CliRunner().invoke(cli_module.main, ["--tree"])
    finally:
        sys.modules.pop("chatgame.cli", None)
        importlib.import_module("chatgame.cli")

    assert result.exit_code == 0
    assert result.output.strip() == render_click_tree(main, root_name="chatgame")
    assert result.output.splitlines()[0] == "chatgame"
    assert result.output.splitlines().count("chatgame") == 1
    assert "--tree  # Print the registered CLI tree and exit." in result.output
    assert "--tree-brief  # Print the registered CLI tree without parameter signatures and exit." in result.output
    assert "solve <IMAGE>" in result.output
    assert "games  # 列出已支持的游戏；只读文本输出。" in result.output
    assert "web  # 管理安装态 Web 服务（后端 + 前端）。" in result.output
    assert "setup  # 检查 Web 运行环境；只读状态输出。" in result.output
    assert "serve [--host HOST]" in result.output
    assert "hello" not in result.output.lower()


def test_tree_brief_renders_same_surface_without_signatures():
    result = CliRunner().invoke(main, ["--tree-brief"])

    assert result.exit_code == 0
    assert result.output.strip() == render_click_tree(main, root_name="chatgame", brief=True)
    assert "games  # 列出已支持的游戏；只读文本输出。" in result.output
    assert "solve  # 解析截图并输出求解步骤；--output 写入标注图。" in result.output
    assert "web  # 管理安装态 Web 服务（后端 + 前端）。" in result.output
    assert "serve  # 启动长驻 Web 服务；监听指定地址和端口。" in result.output
    assert "setup  # 检查 Web 运行环境；只读状态输出。" in result.output
    assert "<IMAGE>" not in result.output
    assert "[--game GAME]" not in result.output
    assert "[--host HOST]" not in result.output


def test_tree_root_uses_public_console_command_in_module_mode():
    result = CliRunner().invoke(main, ["--tree"], prog_name="python -m chatgame.cli")

    assert result.exit_code == 0
    assert result.output.splitlines()[0] == "chatgame"
    assert "python -m chatgame.cli" not in result.output


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
    assert "启动长驻 Web 服务" in result.output


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
