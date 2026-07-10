from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd
import streamlit as st

from database import fetch_df, reset_table


def load_css() -> None:
    try:
        with open("assets/style.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def hero(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def kpi(label: str, value: Any, sub: str = "") -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """


def show_kpis(items: list[tuple[str, Any, str]], cols: int = 4) -> None:
    columns = st.columns(cols)
    for i, item in enumerate(items):
        label, value, sub = item
        with columns[i % cols]:
            st.markdown(kpi(label, value, sub), unsafe_allow_html=True)


def format_currency(value: float | int | None) -> str:
    try:
        return f"AED {float(value):,.0f}"
    except Exception:
        return "AED 0"


def download_excel_button(df: pd.DataFrame, filename: str, label: str = "Download Excel") -> None:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    st.download_button(
        label=label,
        data=output.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )


def editable_table(table_name: str, title: str, key: str, column_config: dict | None = None) -> pd.DataFrame:
    section(title)
    df = fetch_df(f"SELECT * FROM {table_name}")
    edited = st.data_editor(
        df,
        width="stretch",
        hide_index=True,
        num_rows="dynamic",
        column_config=column_config or {},
        key=key,
    )
    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("Save Changes", key=f"save_{key}", width="stretch"):
            reset_table(table_name, edited)
            st.success("Changes saved successfully.")
            st.rerun()
    with c2:
        download_excel_button(edited, f"{table_name}.xlsx", "Export this table")
    return edited


def blank_state(message: str) -> None:
    st.info(message)


def status_badge(status: str) -> str:
    color = "blue"
    if status in ["Expired", "Rejected", "Pending", "Critical"]:
        color = "red"
    elif status in ["Expiring Soon", "Hold", "Submitted", "In Progress"]:
        color = "yellow"
    elif status in ["Valid", "Joined", "Completed", "Paid", "Selected", "Active", "Received"]:
        color = "green"
    elif status in ["Offer Sent", "Shortlisted", "Interview Scheduled"]:
        color = "purple"
    return f'<span class="badge badge-{color}">{status}</span>'


def safe_sum(df: pd.DataFrame, column: str) -> float:
    if df.empty or column not in df.columns:
        return 0
    return pd.to_numeric(df[column], errors="coerce").fillna(0).sum()

