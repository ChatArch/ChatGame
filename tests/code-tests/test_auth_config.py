import base64
import hashlib
import os

import pytest

from chatgame.auth import ChatGameConfig, auth_configured, build_auth, runtime_dir
from chatlogin import Principal, Role


def _hash(password="secret", *, iterations=1000):
    salt = b"0123456789abcdef"
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return "pbkdf2_sha256$%s$%s$%s" % (
        iterations,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def test_auth_is_disabled_without_explicit_account():
    assert auth_configured({}) is False
    assert build_auth({}) is None
    assert build_auth({"CHATGAME_AUTH_TTL_SECONDS": "86400"}) is None


def test_partial_account_config_is_an_error():
    with pytest.raises(ValueError, match="both username and password hash"):
        auth_configured({"CHATGAME_AUTH_USERNAME": "solver"})

    with pytest.raises(ValueError, match="both username and password hash"):
        auth_configured({"CHATGAME_AUTH_PASSWORD_PBKDF2": _hash()})


def test_optional_auth_fields_without_account_are_configuration_errors():
    explicit_fields = [
        ("CHATGAME_AUTH_ORIGIN", "http://testserver"),
        ("CHATGAME_AUTH_USER_ID", "acct-solver"),
        ("CHATGAME_AUTH_DISPLAY_NAME", "Puzzle Solver"),
    ]

    for key, value in explicit_fields:
        with pytest.raises(ValueError, match="username and password hash"):
            build_auth({key: value})


def test_explicit_malformed_ttl_without_account_is_a_configuration_error():
    for ttl in ("invalid", "0", "-10"):
        with pytest.raises(ValueError, match="TTL"):
            build_auth({"CHATGAME_AUTH_TTL_SECONDS": ttl})


def test_auth_builds_shared_login_service_with_private_runtime_path(tmp_path, monkeypatch):
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "home"))
    auth = build_auth(
        {
            "CHATGAME_AUTH_USERNAME": "solver",
            "CHATGAME_AUTH_PASSWORD_PBKDF2": _hash(),
            "CHATGAME_AUTH_USER_ID": "acct-solver",
            "CHATGAME_AUTH_DISPLAY_NAME": "Puzzle Solver",
            "CHATGAME_AUTH_ORIGIN": "http://testserver",
            "CHATGAME_AUTH_TTL_SECONDS": "60",
        }
    )

    assert auth is not None
    assert auth.cookie.name == "chatgame_session"
    assert auth.cookie.max_age == 60
    assert auth.cookie.secure is False
    assert runtime_dir() == tmp_path / "home" / "chatgame"


def test_account_rotation_invalidates_existing_persistent_session(tmp_path, monkeypatch):
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "home"))
    values_a = {
        "CHATGAME_AUTH_USERNAME": "solver",
        "CHATGAME_AUTH_PASSWORD_PBKDF2": _hash("secret-a"),
        "CHATGAME_AUTH_USER_ID": "acct-a",
        "CHATGAME_AUTH_DISPLAY_NAME": "Account A",
        "CHATGAME_AUTH_ORIGIN": "http://testserver",
    }
    auth_a = build_auth(values_a)
    issued = auth_a.sessions.issue(Principal("acct-a", "Account A", Role.USER))
    assert auth_a.sessions.resolve(issued.token) is not None

    auth_b = build_auth(
        {
            **values_a,
            "CHATGAME_AUTH_PASSWORD_PBKDF2": _hash("secret-b"),
            "CHATGAME_AUTH_USER_ID": "acct-b",
            "CHATGAME_AUTH_DISPLAY_NAME": "Account B",
        }
    )

    assert auth_b.sessions.resolve(issued.token) is None


def test_auth_rejects_incomplete_or_malformed_account_config():
    with pytest.raises(ValueError, match="ORIGIN"):
        build_auth({"CHATGAME_AUTH_USERNAME": "solver", "CHATGAME_AUTH_PASSWORD_PBKDF2": _hash()})

    with pytest.raises(ValueError, match="PBKDF2"):
        build_auth(
            {
                "CHATGAME_AUTH_USERNAME": "solver",
                "CHATGAME_AUTH_PASSWORD_PBKDF2": "plain-password",
                "CHATGAME_AUTH_ORIGIN": "http://testserver",
            }
        )

    with pytest.raises(ValueError, match="TTL"):
        build_auth(
            {
                "CHATGAME_AUTH_USERNAME": "solver",
                "CHATGAME_AUTH_PASSWORD_PBKDF2": _hash(),
                "CHATGAME_AUTH_ORIGIN": "http://testserver",
                "CHATGAME_AUTH_TTL_SECONDS": "0",
            }
        )


def test_chatenv_schema_marks_password_hash_sensitive():
    fields = ChatGameConfig.get_fields()

    assert fields["CHATGAME_AUTH_PASSWORD_PBKDF2"].is_sensitive is True
    assert fields["CHATGAME_AUTH_USERNAME"].is_sensitive is False
    assert os.path.basename(str(runtime_dir())) == "chatgame"
