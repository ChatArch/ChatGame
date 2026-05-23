import importlib
import io
import sys

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from conftest import IMG_10x10_32660_CROP


def _load_api(monkeypatch, assets_dir=None, disable_ui=False):
    if assets_dir is not None:
        monkeypatch.setenv("CHATGAME_WEB_ASSETS_DIR", str(assets_dir))
    else:
        monkeypatch.delenv("CHATGAME_WEB_ASSETS_DIR", raising=False)

    if disable_ui:
        monkeypatch.setenv("CHATGAME_DISABLE_WEB_UI", "1")
    else:
        monkeypatch.delenv("CHATGAME_DISABLE_WEB_UI", raising=False)

    sys.modules.pop("chatgame.api", None)
    module = importlib.import_module("chatgame.api")
    return importlib.reload(module)


def test_api_routes_support_prefixed_and_unprefixed_paths(monkeypatch):
    api = _load_api(monkeypatch, disable_ui=True)
    client = TestClient(api.app)

    assert client.get("/health").status_code == 200
    assert client.get("/api/health").status_code == 200

    games_plain = client.get("/games")
    games_api = client.get("/api/games")

    assert games_plain.status_code == 200
    assert games_api.status_code == 200
    assert games_plain.json() == games_api.json()
    assert games_plain.json()["games"][0]["id"] == "cow-puzzle"


def test_api_serves_static_assets_and_spa_fallback(tmp_path, monkeypatch):
    assets_dir = tmp_path / "dist"
    assets_dir.mkdir()
    (assets_dir / "index.html").write_text("<html>chatgame</html>", encoding="utf-8")
    (assets_dir / "app.js").write_text("console.log('ok')", encoding="utf-8")

    api = _load_api(monkeypatch, assets_dir=assets_dir)
    client = TestClient(api.app)

    assert client.get("/").status_code == 200
    assert "chatgame" in client.get("/").text
    assert client.get("/app.js").status_code == 200
    assert "console.log" in client.get("/app.js").text
    assert client.get("/solve-game").status_code == 200
    assert "chatgame" in client.get("/solve-game").text


def test_api_reads_game_docs_from_packaged_directory(tmp_path, monkeypatch):
    docs_dir = tmp_path / "docs" / "games" / "cow-puzzle"
    docs_dir.mkdir(parents=True)
    (docs_dir / "rules.md").write_text("规则正文", encoding="utf-8")
    (docs_dir / "strategy.md").write_text("攻略正文", encoding="utf-8")

    api = _load_api(monkeypatch, disable_ui=True)
    monkeypatch.setattr(api, "_DOCS_DIR", tmp_path / "docs" / "games")
    client = TestClient(api.app)

    response = client.get("/api/games/cow-puzzle/docs")

    assert response.status_code == 200
    assert response.json() == {
        "rules": "规则正文",
        "strategy": "攻略正文",
    }


def test_api_returns_404_when_web_ui_disabled(monkeypatch):
    api = _load_api(monkeypatch, disable_ui=True)
    client = TestClient(api.app)

    response = client.get("/")

    assert response.status_code == 404


def test_solve_returns_warning_for_non_unique_solution(monkeypatch, mocker):
    api = _load_api(monkeypatch, disable_ui=True)
    client = TestClient(api.app)
    image_buf = io.BytesIO()
    Image.new("RGB", (1, 1), (255, 255, 255)).save(image_buf, format="PNG")

    mocker.patch(
        "chatgame.games.cow_puzzle.parse.parse",
        return_value=(np.array([[0]]), np.array([[[128, 185, 254]]], dtype=np.uint8), (0, 0, 10, 10)),
    )
    mocker.patch(
        "chatgame.games.cow_puzzle.solver.find_solutions",
        return_value=[[(0, 0)], [(0, 0)]],
    )

    response = client.post(
        "/api/solve",
        data={"game": "cow-puzzle", "n": "1"},
        files={"image": ("board.png", image_buf.getvalue(), "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["solution_status"] == "multiple"
    assert "多个合法解" in data["message"]
    assert data["steps"][0]["row"] == 0
    assert data["steps"][0]["col"] == 0


def test_solve_auto_detects_10x10_upload_without_size(monkeypatch):
    api = _load_api(monkeypatch, disable_ui=True)
    client = TestClient(api.app)

    response = client.post(
        "/api/solve",
        data={"game": "cow-puzzle"},
        files={
            "image": (
                IMG_10x10_32660_CROP.name,
                IMG_10x10_32660_CROP.read_bytes(),
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["n"] == 10
    assert data["solution_status"] == "multiple"
    assert "多个合法解" in data["message"]
    assert len(data["steps"]) == 10
