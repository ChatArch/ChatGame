import importlib
import io
import base64
import hashlib
import os
import sys
import time

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from conftest import IMG_10x10_32660_CROP


def _pbkdf2_config(password="secret", *, iterations=1000):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return (
        "pbkdf2_sha256$"
        f"{iterations}$"
        f"{base64.b64encode(salt).decode('ascii')}$"
        f"{base64.b64encode(digest).decode('ascii')}"
    )


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
    sys.modules.pop("chatgame.auth", None)
    module = importlib.import_module("chatgame.api")
    return importlib.reload(module)


def _configure_auth(monkeypatch, tmp_path, *, password="secret", ttl="86400"):
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("CHATGAME_AUTH_USERNAME", "solver")
    monkeypatch.setenv("CHATGAME_AUTH_PASSWORD_PBKDF2", _pbkdf2_config(password))
    monkeypatch.setenv("CHATGAME_AUTH_USER_ID", "acct-solver")
    monkeypatch.setenv("CHATGAME_AUTH_DISPLAY_NAME", "Puzzle Solver")
    monkeypatch.setenv("CHATGAME_AUTH_ORIGIN", "http://testserver")
    monkeypatch.setenv("CHATGAME_AUTH_TTL_SECONDS", ttl)


def test_api_routes_support_prefixed_and_unprefixed_paths(monkeypatch):
    api = _load_api(monkeypatch, disable_ui=True)
    client = TestClient(api.app)

    assert api.app.version == "0.1.13"
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


def test_auth_bootstrap_is_guest_without_config_and_solver_stays_public(monkeypatch):
    api = _load_api(monkeypatch, disable_ui=True)
    client = TestClient(api.app)

    bootstrap = client.get("/api/auth/bootstrap")
    login = client.get("/login")
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

    assert bootstrap.status_code == 200
    assert bootstrap.json()["auth_available"] is False
    assert bootstrap.json()["identity"] == "guest"
    assert bootstrap.json()["login_url"] is None
    assert login.status_code == 404
    assert response.status_code == 200


def test_configured_auth_login_session_logout_and_csrf(tmp_path, monkeypatch):
    _configure_auth(monkeypatch, tmp_path)
    api = _load_api(monkeypatch, disable_ui=True)
    client = TestClient(api.app)

    bootstrap = client.get("/api/auth/bootstrap")
    assert bootstrap.status_code == 200
    assert bootstrap.json()["auth_available"] is True
    assert bootstrap.json()["identity"] == "guest"
    assert bootstrap.json()["login_url"] == "/login"

    bad = client.post(
        "/api/auth/login",
        json={"username": "solver", "password": "wrong"},
        headers={"origin": "http://testserver", "sec-fetch-site": "same-origin"},
    )
    assert bad.status_code == 401

    logged_in = client.post(
        "/api/auth/login",
        json={"username": "solver", "password": "secret"},
        headers={"origin": "http://testserver", "sec-fetch-site": "same-origin"},
    )
    assert logged_in.status_code == 200
    data = logged_in.json()
    assert data["authenticated"] is True
    assert data["user"] == {"user_id": "acct-solver", "display_name": "Puzzle Solver", "role": "user"}
    assert "secret" not in logged_in.text
    csrf = data["csrf_token"]

    session = client.get("/api/auth/session")
    assert session.status_code == 200
    assert session.json()["identity"] == "authenticated"
    assert session.json()["user"]["user_id"] == "acct-solver"

    no_csrf = client.post(
        "/api/auth/logout",
        headers={"origin": "http://testserver", "sec-fetch-site": "same-origin"},
    )
    assert no_csrf.status_code == 403

    logged_out = client.post(
        "/api/auth/logout",
        headers={
            "origin": "http://testserver",
            "sec-fetch-site": "same-origin",
            "x-csrf-token": csrf,
        },
    )
    assert logged_out.status_code == 200
    assert client.get("/api/auth/session").json()["identity"] == "guest"


def test_configured_auth_rejects_cross_origin_and_invalid_cookie(tmp_path, monkeypatch):
    _configure_auth(monkeypatch, tmp_path)
    api = _load_api(monkeypatch, disable_ui=True)
    client = TestClient(api.app)

    blocked = client.post(
        "/api/auth/login",
        json={"username": "solver", "password": "secret"},
        headers={"origin": "http://evil.example", "sec-fetch-site": "cross-site"},
    )
    assert blocked.status_code == 403

    client.cookies.set("chatgame_session", "not-a-valid-session-token-for-chatgame", domain="testserver")
    session = client.get("/api/auth/session")
    assert session.status_code == 200
    assert session.json()["identity"] == "guest"


def test_configured_auth_session_expires_by_ttl(tmp_path, monkeypatch):
    _configure_auth(monkeypatch, tmp_path, ttl="1")
    api = _load_api(monkeypatch, disable_ui=True)
    client = TestClient(api.app)

    logged_in = client.post(
        "/api/auth/login",
        json={"username": "solver", "password": "secret"},
        headers={"origin": "http://testserver", "sec-fetch-site": "same-origin"},
    )
    assert logged_in.status_code == 200
    time.sleep(1.1)

    session = client.get("/api/auth/session")

    assert session.status_code == 200
    assert session.json()["identity"] == "guest"


def test_auth_uses_chatenv_active_config_and_private_runtime_path(tmp_path, monkeypatch):
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "home"))
    env_dir = tmp_path / "home" / "envs" / "ChatGame"
    env_dir.mkdir(parents=True)
    env_file = env_dir / ".env"
    env_file.write_text(
        "\n".join(
            [
                "CHATGAME_AUTH_USERNAME='solver'",
                f"CHATGAME_AUTH_PASSWORD_PBKDF2='{_pbkdf2_config('secret')}'",
                "CHATGAME_AUTH_USER_ID='acct-solver'",
                "CHATGAME_AUTH_DISPLAY_NAME='Puzzle Solver'",
                "CHATGAME_AUTH_ORIGIN='http://testserver'",
            ]
        ),
        encoding="utf-8",
    )
    api = _load_api(monkeypatch, disable_ui=True)
    client = TestClient(api.app)

    assert client.get("/api/auth/bootstrap").json()["auth_available"] is True
    logged_in = client.post(
        "/api/auth/login",
        json={"username": "solver", "password": "secret"},
        headers={"origin": "http://testserver", "sec-fetch-site": "same-origin"},
    )

    assert logged_in.status_code == 200
    runtime_db = tmp_path / "home" / "chatgame" / "auth" / "sessions.sqlite3"
    assert runtime_db.exists()
    assert ".chatgame" not in str(runtime_db)
    assert "secret" not in runtime_db.read_bytes().decode("latin1", errors="ignore")


def test_shared_login_ui_and_assets_are_exposed_when_configured(tmp_path, monkeypatch):
    _configure_auth(monkeypatch, tmp_path)
    api = _load_api(monkeypatch, disable_ui=True)
    client = TestClient(api.app)

    page = client.get("/login?next=/solve")
    script = client.get("/api/auth/assets/login.js")

    assert page.status_code == 200
    assert "ChatGame" in page.text
    assert "/api/auth/login" in page.text
    assert "/solve" in page.text
    assert script.status_code == 200
    assert "application/javascript" in script.headers["content-type"]


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


def test_contribution_prd_review_flow(tmp_path, monkeypatch):
    api = _load_api(monkeypatch, disable_ui=True)
    monkeypatch.setattr(api, "_CONTRIBUTIONS_ROOT", tmp_path / "contributions")
    client = TestClient(api.app)
    image_buf = io.BytesIO()
    Image.new("RGB", (40, 40), (255, 255, 255)).save(image_buf, format="PNG")

    created = client.post(
        "/api/contributions",
        data={
            "name": "数独",
            "rules": "9x9 棋盘，目标是填满数字，每行每列每宫不重复。",
            "target_type": "playable_solver",
        },
        files={"image": ("sudoku.png", image_buf.getvalue(), "image/png")},
    )

    assert created.status_code == 200
    job = created.json()
    assert job["status"] == "understanding_ready"
    assert job["understanding"]["game_type"] == "logic_puzzle"
    assert "uploads" not in str(job.get("image", {}))

    answers = [
        {
            "question_id": question["id"],
            "value": question["options"][0]["value"],
        }
        for question in job["understanding"]["questions"]
    ]
    answered = client.post(f"/api/contributions/{job['id']}/answers", json={"answers": answers})
    assert answered.status_code == 200
    assert answered.json()["status"] == "understanding_ready"

    prd = client.post(f"/api/contributions/{job['id']}/generate-prd")
    assert prd.status_code == 200
    assert prd.json()["status"] == "prd_ready"
    assert "维护者 review" in prd.json()["prd"]

    edited = client.post(
        f"/api/contributions/{job['id']}/edit-prd",
        json={"content": prd.json()["prd"] + "\n## 用户补充\n需要先 review。\n"},
    )
    assert edited.status_code == 200
    assert edited.json()["status"] == "prd_ready"

    submitted = client.post(f"/api/contributions/{job['id']}/submit-review")
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "review_pending"
    assert "GitHub" in submitted.json()["user_message"]

    games = client.get("/api/games").json()["games"]
    pending = [game for game in games if game.get("job_id") == job["id"]]
    assert pending
    assert pending[0]["status"] == "review_pending"
    assert pending[0]["github_url"].startswith("https://github.com/")


def test_contribution_preserves_clarification_labels_in_prd(tmp_path, monkeypatch):
    api = _load_api(monkeypatch, disable_ui=True)
    monkeypatch.setattr(api, "_CONTRIBUTIONS_ROOT", tmp_path / "contributions")
    client = TestClient(api.app)
    image_buf = io.BytesIO()
    Image.new("RGB", (40, 40), (255, 255, 255)).save(image_buf, format="PNG")

    created = client.post(
        "/api/contributions",
        data={
            "name": "网格谜题",
            "rules": "棋盘上需要根据区域限制摆放棋子。",
            "target_type": "playable",
        },
        files={"image": ("grid.png", image_buf.getvalue(), "image/png")},
    )

    assert created.status_code == 200
    job = created.json()
    assert job["status"] == "needs_clarification"

    answers = [
        {
            "question_id": question["id"],
            "value": question["options"][0]["value"],
        }
        for question in job["understanding"]["questions"]
    ]
    answered = client.post(f"/api/contributions/{job['id']}/answers", json={"answers": answers})
    assert answered.status_code == 200

    prd = client.post(f"/api/contributions/{job['id']}/generate-prd")

    assert prd.status_code == 200
    prd_text = prd.json()["prd"]
    assert "第一版棋盘结构如何限定" in prd_text
    assert "固定行列网格" in prd_text


def test_contribution_rejects_non_image_upload(tmp_path, monkeypatch):
    api = _load_api(monkeypatch, disable_ui=True)
    monkeypatch.setattr(api, "_CONTRIBUTIONS_ROOT", tmp_path / "contributions")
    client = TestClient(api.app)

    response = client.post(
        "/api/contributions",
        data={"name": "测试", "rules": "规则", "target_type": "docs_only"},
        files={"image": ("notes.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400
    assert "PNG" in response.json()["detail"]


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
