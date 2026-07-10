from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from pathlib import Path
from urllib.parse import urlencode

import streamlit as st

from config import ATTENDANCE_PORTAL_URL


def _sso_config() -> dict:
    project_secrets = Path(__file__).resolve().parents[1] / ".streamlit" / "secrets.toml"
    user_secrets = Path.home() / ".streamlit" / "secrets.toml"
    if not project_secrets.exists() and not user_secrets.exists():
        return {}

    try:
        return dict(st.secrets.get("attendance_sso", {}))
    except Exception:
        return {}


def _urlsafe_b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _sign(payload: str, shared_secret: str) -> str:
    digest = hmac.new(shared_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return _urlsafe_b64(digest)


def is_configured() -> bool:
    return bool(_sso_config().get("shared_secret"))


def build_launch_url(user: dict) -> str:
    config = _sso_config()
    shared_secret = config.get("shared_secret", "")
    if not shared_secret:
        return ATTENDANCE_PORTAL_URL

    ttl = int(config.get("token_ttl_seconds", 300))
    expires_at = int(time.time()) + ttl
    params = {
        "sso_email": user.get("username", ""),
        "sso_name": user.get("full_name", "Admin"),
        "sso_role": user.get("role", ""),
        "sso_exp": str(expires_at),
        "sso_nonce": secrets.token_urlsafe(16),
    }
    payload = "&".join(f"{key}={params[key]}" for key in sorted(params))
    params["sso_sig"] = _sign(payload, shared_secret)
    return f"{ATTENDANCE_PORTAL_URL}?{urlencode(params)}"
