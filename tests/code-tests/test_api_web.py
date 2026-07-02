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


def test_contribution_wizard_generates_and_approves_prd(tmp_path, monkeypatch):
    monkeypatch.setenv("CHATGAME_CONTRIBUTIONS_DIR", str(tmp_path / "contributions"))
    api = _load_api(monkeypatch, disable_ui=True)
    client = TestClient(api.app)
    image_buf = io.BytesIO()
    Image.new("RGB", (8, 8), (255, 255, 255)).save(image_buf, format="PNG")

    response = client.post(
        "/api/contributions",
        data={
            "name": "数独",
            "target": "play_and_solve",
            "rules": "9x9 数独，每行每列和每个 3x3 宫都不能重复，填满后过关。",
        },
        files={"image": ("sudoku.png", image_buf.getvalue(), "image/png")},
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "needs_clarification"
    question_ids = {question["id"] for question in job["understanding"]["questions"]}
    assert {"solver_output", "screenshot_parse", "scope_version"}.issubset(question_ids)

    response = client.post(
        f"/api/contributions/{job['job_id']}/answers",
        json={
            "answers": [
                {"question_id": "solver_output", "value": "full_solution"},
                {"question_id": "screenshot_parse", "value": "later"},
                {"question_id": "scope_version", "value": "prd_only"},
            ]
        },
    )

    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "understanding_ready"
    assert job["understanding"]["sufficient"] is True

    response = client.post(f"/api/contributions/{job['job_id']}/generate-prd")
    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "prd_ready"
    assert "# 数独 接入 PRD" in job["prd"]

    response = client.post(f"/api/contributions/{job['job_id']}/approve-prd")
    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "review_pending"
    assert "维护者 review" in job["review"]["message"]

    games = client.get("/api/games").json()["games"]
    pending = [game for game in games if game.get("status") == "pending_review"]
    assert pending[0]["name"] == "数独"
    assert pending[0]["badge"] == "待评审"

    artifact = client.get(f"/api/contributions/{job['job_id']}/artifacts/PRD.md")
    assert artifact.status_code == 200
    assert "安全约束" in artifact.text


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
