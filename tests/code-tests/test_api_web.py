import importlib
import sys

from fastapi.testclient import TestClient


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


def test_api_returns_404_when_web_ui_disabled(monkeypatch):
    api = _load_api(monkeypatch, disable_ui=True)
    client = TestClient(api.app)

    response = client.get("/")

    assert response.status_code == 404
