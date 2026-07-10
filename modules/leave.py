from __future__ import annotations

import streamlit as st

from config import LEAVE_TYPES
from database import execute, fetch_df
from modules.components import editable_table, hero, section


def show() -> None:
    hero("Leave Management", "Track annual leave, sick leave, emergency leave and unpaid leave balances by employee.")

    with st.expander("Add Leave Balance", expanded=True):
        with st.form("leave_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            employee = c1.text_input("Employee")
            leave_type = c2.selectbox("Leave Type", LEAVE_TYPES)
            opening_balance = c3.number_input("Opening Balance", min_value=0.0, step=0.5, value=30.0)
            used = c1.number_input("Used", min_value=0.0, step=0.5)
            remaining = max(float(opening_balance) - float(used), 0)
            c2.metric("Remaining", f"{remaining:.1f}")
            submit = st.form_submit_button("Save Leave Record", width="stretch")
            if submit:
                if not employee:
                    st.error("Employee name is required.")
                else:
                    execute(
                        "INSERT INTO leave_management(employee, leave_type, opening_balance, used, remaining) VALUES (?, ?, ?, ?, ?)",
                        (employee, leave_type, float(opening_balance), float(used), float(remaining)),
                    )
                    st.success("Leave balance saved.")
                    st.rerun()

    df = fetch_df("SELECT * FROM leave_management")
    section("Leave Balance Summary")
    if df.empty:
        st.info("No leave records yet.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Employees in Leave Register", df["employee"].nunique())
        c2.metric("Total Used", f"{df['used'].sum():.1f}")
        c3.metric("Total Remaining", f"{df['remaining'].sum():.1f}")
        st.dataframe(df, width="stretch", hide_index=True)

    editable_table("leave_management", "Leave Management Table", "leave_table")

