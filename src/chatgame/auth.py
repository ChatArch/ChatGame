"""Optional shared-account authentication for ChatGame."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

from chatenv import BaseEnvConfig, EnvField, EnvStore, get_paths
from chatlogin import (
    PasswordBackend,
    PasswordHash,
    Principal,
    Role,
    SQLiteSessionStore,
    SessionManager,
)
from chatlogin.fastapi import CookieSettings, FastAPIAuth
from chatlogin.ui import LoginUI


class ChatGameConfig(BaseEnvConfig):
    """ChatEnv schema for the optional ChatGame account."""

    _title = "ChatGame Configuration"
    _aliases = ["chatgame", "game"]
    _storage_dir = "ChatGame"

    CHATGAME_AUTH_USERNAME = EnvField(
        "CHATGAME_AUTH_USERNAME",
        desc="Explicit ChatGame login username. Leave empty to keep auth disabled.",
    )
    CHATGAME_AUTH_PASSWORD_PBKDF2 = EnvField(
        "CHATGAME_AUTH_PASSWORD_PBKDF2",
        desc="PBKDF2 password hash: pbkdf2_sha256$iterations$salt_b64$digest_b64.",
        is_sensitive=True,
    )
    CHATGAME_AUTH_USER_ID = EnvField(
        "CHATGAME_AUTH_USER_ID",
        desc="Stable account id exposed in authenticated session payload.",
    )
    CHATGAME_AUTH_DISPLAY_NAME = EnvField(
        "CHATGAME_AUTH_DISPLAY_NAME",
        desc="Display name exposed in authenticated session payload.",
    )
    CHATGAME_AUTH_ORIGIN = EnvField(
        "CHATGAME_AUTH_ORIGIN",
        default="",
        desc="Canonical http(s) origin for same-origin login and logout requests.",
    )
    CHATGAME_AUTH_TTL_SECONDS = EnvField(
        "CHATGAME_AUTH_TTL_SECONDS",
        default="86400",
        desc="Session TTL in seconds.",
    )


def runtime_dir() -> Path:
    return get_paths().home_dir / "chatgame"


def _load_values() -> dict[str, str]:
    values = EnvStore(get_paths().envs_dir).load_active(ChatGameConfig)
    for field in ChatGameConfig.get_fields().values():
        env_value = os.getenv(field.env_key)
        if env_value is not None:
            values[field.env_key] = env_value
    return values


def _parse_password_hash(value: str) -> PasswordHash:
    parts = value.split("$")
    if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
        raise ValueError("CHATGAME_AUTH_PASSWORD_PBKDF2 must use pbkdf2_sha256$iterations$salt_b64$digest_b64")
    try:
        iterations = int(parts[1])
        salt = base64.b64decode(parts[2].encode("ascii"), validate=True)
        digest = base64.b64decode(parts[3].encode("ascii"), validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("CHATGAME_AUTH_PASSWORD_PBKDF2 is malformed") from exc
    return PasswordHash(salt=salt, digest=digest, iterations=iterations)


def _parse_ttl(value: str) -> int:
    try:
        ttl = int(value)
    except ValueError as exc:
        raise ValueError("CHATGAME_AUTH_TTL_SECONDS must be an integer") from exc
    if ttl <= 0:
        raise ValueError("CHATGAME_AUTH_TTL_SECONDS must be positive")
    return ttl


def auth_configured(values: dict[str, str] | None = None) -> bool:
    values = values if values is not None else _load_values()
    has_username = bool(values.get("CHATGAME_AUTH_USERNAME"))
    has_hash = bool(values.get("CHATGAME_AUTH_PASSWORD_PBKDF2"))
    if has_username != has_hash:
        raise ValueError("ChatGame auth requires both username and password hash, or neither")
    if not has_username:
        has_explicit_auth_metadata = any(
            bool(values.get(key))
            for key in (
                "CHATGAME_AUTH_ORIGIN",
                "CHATGAME_AUTH_USER_ID",
                "CHATGAME_AUTH_DISPLAY_NAME",
            )
        )
        if has_explicit_auth_metadata:
            raise ValueError("ChatGame auth requires username and password hash when auth fields are configured")
        _parse_ttl(values.get("CHATGAME_AUTH_TTL_SECONDS") or "86400")
    return has_username and has_hash


def _session_instance(values: dict[str, str]) -> str:
    marker = {
        "username": values["CHATGAME_AUTH_USERNAME"],
        "password_hash": values["CHATGAME_AUTH_PASSWORD_PBKDF2"],
        "user_id": values.get("CHATGAME_AUTH_USER_ID") or values["CHATGAME_AUTH_USERNAME"],
        "display_name": values.get("CHATGAME_AUTH_DISPLAY_NAME") or values["CHATGAME_AUTH_USERNAME"],
    }
    encoded = json.dumps(marker, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"chatgame-{hashlib.sha256(encoded).hexdigest()[:24]}"


def build_auth(values: dict[str, str] | None = None) -> FastAPIAuth | None:
    values = values if values is not None else _load_values()
    if not auth_configured(values):
        return None

    origin = values.get("CHATGAME_AUTH_ORIGIN") or ""
    if not origin:
        raise ValueError("CHATGAME_AUTH_ORIGIN is required when ChatGame auth is configured")

    username = values["CHATGAME_AUTH_USERNAME"]
    user_id = values.get("CHATGAME_AUTH_USER_ID") or username
    display_name = values.get("CHATGAME_AUTH_DISPLAY_NAME") or username
    ttl = _parse_ttl(values.get("CHATGAME_AUTH_TTL_SECONDS") or "86400")
    principal = Principal(user_id=user_id, display_name=display_name, role=Role.USER)
    backend = PasswordBackend({username: (principal, _parse_password_hash(values["CHATGAME_AUTH_PASSWORD_PBKDF2"]))})
    store = SQLiteSessionStore(runtime_dir() / "auth" / "sessions.sqlite3", max_sessions=4096)
    sessions = SessionManager(store, instance=_session_instance(values), ttl=ttl)
    secure_cookie = origin.startswith("https://")
    return FastAPIAuth(
        backend,
        sessions,
        origin=origin,
        prefix="/api/auth",
        ui=LoginUI(
            title="ChatGame",
            subtitle="登录共享账号后继续，也可以保持访客身份求解。",
            palette="forest",
            guest_url="/solve",
            guest_label="以访客身份继续求解",
        ),
        cookie=CookieSettings(
            name="chatgame_session",
            secure=secure_cookie,
            same_site="lax",
            max_age=ttl,
        ),
    )


@lru_cache(maxsize=1)
def get_auth() -> FastAPIAuth | None:
    return build_auth()


def clear_auth_cache() -> None:
    get_auth.cache_clear()


__all__ = [
    "ChatGameConfig",
    "auth_configured",
    "build_auth",
    "clear_auth_cache",
    "get_auth",
    "runtime_dir",
]
