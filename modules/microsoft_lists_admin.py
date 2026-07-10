from __future__ import annotations

import pandas as pd
import streamlit as st

from database import fetch_df, reset_table
from modules.components import hero, section
from modules.data_import import TABLES, _db_columns
from modules.microsoft_graph import (
    MicrosoftConfigError,
    append_list_rows,
    fetch_list_df,
    get_config,
    is_configured,
    test_connection,
)


SYNC_TABLES = [
    "employees",
    "recruitment",
    "interview_evaluation",
    "vendors",
    "pantry",
    "tasks",
]


def _configured_table_rows() -> pd.DataFrame:
    try:
        config = get_config()
    except Exception:
        return pd.DataFrame(columns=["Table", "Microsoft List ID", "Status"])

    rows = []
    for table_name in SYNC_TABLES:
        rows.append(
            {
                "Table": TABLES[table_name]["label"],
                "Microsoft List ID": config.lists.get(table_name, ""),
                "Status": "Configured" if config.lists.get(table_name) else "Missing List ID",
            }
        )
    return pd.DataFrame(rows)


def _push_local_to_list(table_name: str) -> None:
    columns = _db_columns(table_name)
    local_df = fetch_df(f"SELECT {', '.join(columns)} FROM {table_name}")
    if local_df.empty:
        st.info("No local rows to push.")
        return
    count = append_list_rows(table_name, local_df)
    st.success(f"Pushed {count} row(s) to {TABLES[table_name]['label']}.")


def _pull_list_to_local(table_name: str) -> None:
    columns = _db_columns(table_name)
    remote_df = fetch_list_df(table_name, columns)
    if remote_df.empty:
        st.info("No Microsoft List rows found.")
        return
    local_df = remote_df[[col for col in columns if col in remote_df.columns]].copy()
    for col in columns:
        if col not in local_df.columns:
            local_df[col] = ""
    local_df = local_df[columns]
    reset_table(table_name, local_df)
    st.success(f"Pulled {len(local_df)} row(s) into local {TABLES[table_name]['label']}.")


def show() -> None:
    hero("Microsoft Lists Setup", "Connect Azure login details and sync Citi Homes data with Microsoft Lists.")

    st.warning(
        "Do not paste client secrets into chat. Add Azure details in `.streamlit/secrets.toml`, then use this page to test and sync."
    )

    section("Connection Status")
    if not is_configured():
        st.info("Microsoft Lists is not configured yet. Use the sample secrets file as a guide.")
    st.dataframe(_configured_table_rows(), hide_index=True, width="stretch")

    if st.button("Test Microsoft Connection", width="stretch"):
        try:
            result = test_connection()
            st.success("Microsoft Graph connection successful.")
            st.caption(f"Site ID: {result['site_id']}")
            st.dataframe(pd.DataFrame(result["available_lists"]), hide_index=True, width="stretch")
        except MicrosoftConfigError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Connection failed: {exc}")

    section("Sync Data")
    table_name = st.selectbox(
        "Select table",
        SYNC_TABLES,
        format_func=lambda value: TABLES[value]["label"],
    )
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Adds local rows into Microsoft Lists. Existing Microsoft rows are kept.")
        if st.button("Push local data to Microsoft List", width="stretch"):
            try:
                _push_local_to_list(table_name)
            except Exception as exc:
                st.error(f"Push failed: {exc}")
    with c2:
        st.caption("Replaces the local table from Microsoft Lists. Use only after checking the Microsoft List.")
        confirm = st.checkbox("I understand this replaces the local selected table.", key="ms_pull_confirm")
        if st.button("Pull Microsoft List into local app", width="stretch"):
            if not confirm:
                st.error("Please tick the confirmation first.")
            else:
                try:
                    _pull_list_to_local(table_name)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Pull failed: {exc}")
