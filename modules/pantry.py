from __future__ import annotations

import streamlit as st

from database import execute, fetch_df
from modules.components import editable_table, format_currency, hero, section
from modules.page_import import import_panel


def show() -> None:
    hero("Pantry Management", "Monthly pantry requirement, usage, closing balance and cost control for office and factory operations.")

    with st.expander("Add Pantry Item", expanded=True):
        with st.form("pantry_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            month = c1.text_input("Month", value="July 2026")
            item = c2.text_input("Item", placeholder="Tea / Coffee / Milk Tins")
            opening = c3.number_input("Opening", min_value=0.0, step=1.0)
            purchased = c1.number_input("Purchased", min_value=0.0, step=1.0)
            used = c2.number_input("Used", min_value=0.0, step=1.0)
            closing = max(opening + purchased - used, 0)
            c3.metric("Closing", f"{closing:.0f}")
            required_next_month = c1.number_input("Required Next Month", min_value=0.0, step=1.0)
            cost = c2.number_input("Cost AED", min_value=0.0, step=10.0)
            submit = st.form_submit_button("Save Pantry Record", width="stretch")
            if submit:
                if not item:
                    st.error("Item name is required.")
                else:
                    execute(
                        "INSERT INTO pantry(month, item, opening, purchased, used, closing, required_next_month, cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (month, item, opening, purchased, used, closing, required_next_month, cost),
                    )
                    st.success("Pantry record saved.")
                    st.rerun()

    df = fetch_df("SELECT * FROM pantry")
    section("Pantry Cost Summary")
    if df.empty:
        st.info("No pantry records yet.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Cost", format_currency(df["cost"].sum()))
        c2.metric("Items", df["item"].nunique())
        c3.metric("Required Next Month", f"{df['required_next_month'].sum():.0f} units")
        st.dataframe(df, width="stretch", hide_index=True)

    editable_table("pantry", "Pantry Tracker Table", "pantry_table")
    import_panel("pantry", "Import Pantry Data")

