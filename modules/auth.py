from __future__ import annotations

from typing import Any

import streamlit as st


def _secret_section(name: str) -> dict[str, Any]:
    try:
        return dict(st.secrets.get(name, {}))
    except Exception:
        return {}


def microsoft_login_enabled() -> bool:
    auth = _secret_section("auth")
    required = ["redirect_uri", "cookie_secret", "client_id", "client_secret", "server_metadata_url"]
    return all(auth.get(key) for key in required)


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip().lower()]
    return [str(item).strip().lower() for item in value if str(item).strip()]


def _user_email() -> str:
    for key in ["email", "preferred_username", "upn"]:
        value = st.user.get(key)
        if value:
            return str(value).strip().lower()
    return ""


def _user_name(email: str) -> str:
    for key in ["name", "given_name"]:
        value = st.user.get(key)
        if value:
            return str(value)
    return email or "Microsoft User"


def _is_allowed(email: str) -> bool:
    access = _secret_section("app_access")
    allowed_emails = set(_as_list(access.get("allowed_emails")))
    admin_emails = set(_as_list(access.get("admins")))
    management_emails = set(_as_list(access.get("management")))
    allowed_domains = set(_as_list(access.get("allowed_domains")))

    if not email:
        return False
    if email in allowed_emails or email in admin_emails or email in management_emails:
        return True
    domain = email.split("@")[-1] if "@" in email else ""
    return domain in allowed_domains


def _role_for(email: str) -> str:
    access = _secret_section("app_access")
    if email in set(_as_list(access.get("management"))):
        return "Management"
    if email in set(_as_list(access.get("admins"))):
        return "Admin"
    return str(access.get("default_role", "Admin"))


def require_microsoft_user() -> dict[str, Any] | None:
    if not microsoft_login_enabled():
        return None

    if not st.user.is_logged_in:
        st.markdown(
            """
            <div class="login-shell">
                <div class="login-logo brand-mark"><span>CH</span></div>
                <div class="login-box">
                    <h1>CITI HOMES</h1>
                    <h3>P&C Administration System</h3>
                    <p>Sign in with your Microsoft account to continue.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Sign in with Microsoft", width="stretch"):
            st.login()
        st.stop()

    email = _user_email()
    if not _is_allowed(email):
        st.error("Your Microsoft account is not authorized for this app.")
        st.caption(email or "No email was returned by Microsoft login.")
        if st.button("Sign out", width="stretch"):
            st.logout()
        st.stop()

    return {
        "username": email,
        "full_name": _user_name(email),
        "role": _role_for(email),
    }
