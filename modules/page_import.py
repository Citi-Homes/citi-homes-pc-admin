from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

from database import append_rows
from modules.data_import import TABLES, _clean_import_df, _db_columns


def _read_uploaded(uploaded) -> pd.DataFrame:
    name = uploaded.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded)
    return pd.read_excel(uploaded)


def _template_bytes(table_name: str) -> bytes:
    output = BytesIO()
    columns = _db_columns(table_name)
    example = {col: "" for col in columns}
    for col, value in TABLES[table_name].get("defaults", {}).items():
        if col in example:
            example[col] = value
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([example]).to_excel(writer, index=False, sheet_name=TABLES[table_name]["label"][:31])
    return output.getvalue()


def _append_rows(table_name: str, df: pd.DataFrame) -> None:
    append_rows(table_name, df)


def import_panel(table_name: str, title: str | None = None) -> None:
    config = TABLES[table_name]
    with st.expander(title or f"Import {config['label']} Data", expanded=False):
        st.caption("Upload Excel or CSV data for this page. Existing records are kept; imported rows are added below them.")
        c1, c2 = st.columns([2, 1])
        with c1:
            uploaded = st.file_uploader(
                "Upload file",
                type=["xlsx", "xls", "csv"],
                key=f"{table_name}_page_import_file",
            )
        with c2:
            st.download_button(
                "Download template",
                data=_template_bytes(table_name),
                file_name=f"{table_name}_import_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
                key=f"{table_name}_page_import_template",
            )

        st.caption(f"Required columns: {', '.join(config['required'])}")
        if uploaded is None:
            return

        try:
            raw = _read_uploaded(uploaded)
            clean, missing, ignored = _clean_import_df(raw, table_name)
        except Exception as exc:
            st.error(f"Could not read this file: {exc}")
            return

        if missing:
            st.error(f"Missing required columns: {', '.join(missing)}")
            return

        st.success(f"Ready to import {len(clean)} row(s).")
        st.dataframe(clean.head(20), hide_index=True, width="stretch")
        if ignored:
            st.caption(f"Ignored extra columns: {', '.join(ignored[:12])}")

        confirm = st.checkbox(
            "I reviewed the preview and want to add these rows.",
            key=f"{table_name}_page_import_confirm",
        )
        if st.button("Import rows", key=f"{table_name}_page_import_submit", width="stretch"):
            if not confirm:
                st.error("Please tick the review confirmation before importing.")
                return
            _append_rows(table_name, clean)
            st.success(f"Imported {len(clean)} row(s) into {config['label']}.")
            st.rerun()
