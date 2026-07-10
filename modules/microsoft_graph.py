from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests
import streamlit as st


GRAPH_ROOT = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]


class MicrosoftConfigError(RuntimeError):
    pass


def _secret_section(name: str) -> dict[str, Any]:
    try:
        return dict(st.secrets.get(name, {}))
    except Exception:
        return {}


@dataclass(frozen=True)
class MicrosoftConfig:
    tenant_id: str
    client_id: str
    client_secret: str
    site_id: str
    lists: dict[str, str]


def get_config() -> MicrosoftConfig:
    microsoft = _secret_section("microsoft")
    list_config = _secret_section("microsoft_lists")
    required = ["tenant_id", "client_id", "client_secret", "site_id"]
    missing = [key for key in required if not microsoft.get(key)]
    if missing:
        raise MicrosoftConfigError(f"Missing Microsoft setting(s): {', '.join(missing)}")

    return MicrosoftConfig(
        tenant_id=str(microsoft["tenant_id"]),
        client_id=str(microsoft["client_id"]),
        client_secret=str(microsoft["client_secret"]),
        site_id=str(microsoft["site_id"]),
        lists={str(key): str(value) for key, value in dict(list_config).items() if value},
    )


def is_configured() -> bool:
    try:
        config = get_config()
    except Exception:
        return False
    return bool(config.lists)


def _token(config: MicrosoftConfig) -> str:
    try:
        import msal
    except ImportError as exc:
        raise MicrosoftConfigError("The msal package is not installed. Run: pip install msal") from exc

    app = msal.ConfidentialClientApplication(
        client_id=config.client_id,
        client_credential=config.client_secret,
        authority=f"https://login.microsoftonline.com/{config.tenant_id}",
    )
    result = app.acquire_token_silent(GRAPH_SCOPE, account=None) or app.acquire_token_for_client(scopes=GRAPH_SCOPE)
    if "access_token" not in result:
        error = result.get("error_description") or result.get("error") or "Could not get Microsoft Graph token."
        raise MicrosoftConfigError(error)
    return str(result["access_token"])


def _headers(config: MicrosoftConfig) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_token(config)}",
        "Content-Type": "application/json",
    }


def _request(method: str, url: str, *, config: MicrosoftConfig, **kwargs: Any) -> dict[str, Any]:
    response = requests.request(method, url, headers=_headers(config), timeout=45, **kwargs)
    if response.status_code >= 400:
        raise MicrosoftConfigError(f"Microsoft Graph error {response.status_code}: {response.text[:500]}")
    return response.json() if response.content else {}


def table_list_id(table_name: str, config: MicrosoftConfig | None = None) -> str:
    config = config or get_config()
    list_id = config.lists.get(table_name)
    if not list_id:
        raise MicrosoftConfigError(f"No Microsoft List ID configured for '{table_name}'.")
    return list_id


def fetch_list_df(table_name: str, columns: list[str]) -> pd.DataFrame:
    config = get_config()
    list_id = table_list_id(table_name, config)
    fields = ",".join(columns)
    url = f"{GRAPH_ROOT}/sites/{config.site_id}/lists/{list_id}/items?expand=fields(select={fields})"
    rows: list[dict[str, Any]] = []

    while url:
        payload = _request("GET", url, config=config)
        for item in payload.get("value", []):
            row = dict(item.get("fields", {}))
            row["ms_list_item_id"] = item.get("id")
            rows.append(row)
        url = payload.get("@odata.nextLink")

    return pd.DataFrame(rows)


def append_list_rows(table_name: str, rows: pd.DataFrame) -> int:
    config = get_config()
    list_id = table_list_id(table_name, config)
    url = f"{GRAPH_ROOT}/sites/{config.site_id}/lists/{list_id}/items"
    count = 0

    for _, row in rows.fillna("").iterrows():
        fields = {str(col): value for col, value in row.items() if col != "id"}
        _request("POST", url, config=config, json={"fields": fields})
        count += 1
    return count


def update_list_item(table_name: str, item_id: str, fields: dict[str, Any]) -> None:
    config = get_config()
    list_id = table_list_id(table_name, config)
    url = f"{GRAPH_ROOT}/sites/{config.site_id}/lists/{list_id}/items/{item_id}/fields"
    _request("PATCH", url, config=config, json=fields)


def test_connection() -> dict[str, Any]:
    config = get_config()
    url = f"{GRAPH_ROOT}/sites/{config.site_id}/lists"
    payload = _request("GET", url, config=config)
    return {
        "site_id": config.site_id,
        "configured_lists": config.lists,
        "available_lists": [
            {"name": item.get("name"), "displayName": item.get("displayName"), "id": item.get("id")}
            for item in payload.get("value", [])
        ],
    }
