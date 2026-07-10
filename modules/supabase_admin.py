from __future__ import annotations

import streamlit as st

from modules.components import hero, section, show_kpis
from modules.supabase_client import fetch_rows, is_configured, table_count, test_connection


TABLES = [
    "users",
    "employees",
    "recruitment",
    "interview_evaluation",
    "joining_checklist",
    "attendance",
    "leave_management",
    "documents",
    "pantry",
    "utilities",
    "inventory",
    "vendors",
    "tasks",
]


def show() -> None:
    hero(
        "Supabase Setup",
        "Prepare secure online storage for the P&C Administration System while keeping the local app working.",
    )

    st.info(
        "Use Supabase as the online database. Keep the service role key only inside Streamlit secrets; do not paste it into GitHub or public pages."
    )

    section("Connection")
    if not is_configured():
        st.warning("Supabase is not configured yet. Add your project URL and service role key in `.streamlit/secrets.toml`.")
    if st.button("Test Supabase Connection", width="stretch"):
        ok, message = test_connection()
        if ok:
            st.success(message)
        else:
            st.error(message)

    section("Online Table Counts")
    if st.button("Refresh Supabase Counts", width="stretch"):
        counts = []
        for table in TABLES:
            try:
                counts.append((table.replace("_", " ").title(), table_count(table), "rows online"))
            except Exception:
                counts.append((table.replace("_", " ").title(), "Not ready", "check schema/secrets"))
        show_kpis(counts[:4], cols=4)
        show_kpis(counts[4:8], cols=4)
        show_kpis(counts[8:12], cols=4)
        show_kpis(counts[12:], cols=4)

    section("Quick Preview")
    table = st.selectbox("Preview table", TABLES)
    if st.button("Load Preview", width="stretch"):
        try:
            st.dataframe(fetch_rows(table, limit=20), width="stretch", hide_index=True)
        except Exception as exc:
            st.error(f"Could not load `{table}` from Supabase: {exc}")

    section("Next Step")
    st.markdown(
        """
        1. Create the free Supabase project.
        2. Run `scripts/supabase_schema.sql` inside the Supabase SQL Editor.
        3. Add the Supabase secrets locally.
        4. Run `scripts/migrate_sqlite_to_supabase.py` once to copy the current local data online.
        """
    )
