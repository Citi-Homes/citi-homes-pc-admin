from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import pandas as pd
import requests
import streamlit as st


@dataclass(frozen=True)
class SupabaseConfig:
    url: str
    key: str


class SupabaseConfigError(RuntimeError):
    pass


def get_config() -> SupabaseConfig:
    try:
        config = st.secrets.get("supabase", {})
    except Exception as exc:
        raise SupabaseConfigError("Supabase secrets are not configured yet.") from exc

    url = str(config.get("url") or "").strip().rstrip("/")
    key = str(config.get("service_role_key") or config.get("anon_key") or "").strip()
    if not url or not key:
        raise SupabaseConfigError("Add your Supabase URL and service role key in .streamlit/secrets.toml.")
    return SupabaseConfig(url=url, key=key)


def is_configured() -> bool:
    try:
        get_config()
    except SupabaseConfigError:
        return False
    return True


def _headers(config: SupabaseConfig) -> dict[str, str]:
    return {
        "apikey": config.key,
        "Authorization": f"Bearer {config.key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


def fetch_rows(table: str, limit: int = 1000) -> pd.DataFrame:
    config = get_config()
    params = urlencode({"select": "*", "order": "id.asc", "limit": limit})
    response = requests.get(
        f"{config.url}/rest/v1/{table}?{params}",
        headers=_headers(config),
        timeout=20,
    )
    response.raise_for_status()
    return pd.DataFrame(response.json())


def table_count(table: str) -> int:
    config = get_config()
    response = requests.get(
        f"{config.url}/rest/v1/{table}?select=id",
        headers={**_headers(config), "Range": "0-0", "Prefer": "count=exact"},
        timeout=20,
    )
    response.raise_for_status()
    content_range = response.headers.get("content-range", "")
    if "/" in content_range:
        total = content_range.rsplit("/", 1)[-1]
        if total.isdigit():
            return int(total)
    return len(response.json())


def upsert_rows(table: str, rows: list[dict[str, Any]], conflict_column: str = "id") -> int:
    if not rows:
        return 0
    config = get_config()
    response = requests.post(
        f"{config.url}/rest/v1/{table}?on_conflict={conflict_column}",
        headers={**_headers(config), "Prefer": "resolution=merge-duplicates,return=minimal"},
        json=rows,
        timeout=60,
    )
    response.raise_for_status()
    return len(rows)


def test_connection() -> tuple[bool, str]:
    try:
        count = table_count("users")
    except SupabaseConfigError as exc:
        return False, str(exc)
    except requests.HTTPError as exc:
        return False, f"Supabase responded with an error: {exc.response.text[:250]}"
    except requests.RequestException as exc:
        return False, f"Could not connect to Supabase: {exc}"
    return True, f"Connected successfully. Users table has {count} record(s)."
