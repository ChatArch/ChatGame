from click.testing import CliRunner
from chatgame.cli import main
from conftest import IMG_8x8, IMG_10x10


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
