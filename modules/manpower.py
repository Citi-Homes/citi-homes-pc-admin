from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config import DEPARTMENTS, DESIGNATIONS, PRIORITY
from database import execute, fetch_df
from modules.components import editable_table, hero, section


def show() -> None:
    hero("Manpower Planning", "Plan required positions, available manpower, hiring gaps and priority levels before factory operations scale.")

    with st.expander("Add Manpower Requirement", expanded=True):
        with st.form("manpower_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            department = c1.selectbox("Department", DEPARTMENTS)
            position = c2.selectbox("Position", DESIGNATIONS)
            required = c3.number_input("Required", min_value=0, step=1)
            available = c1.number_input("Available", min_value=0, step=1)
            priority = c2.selectbox("Priority", PRIORITY, index=2)
            status = c3.selectbox("Status", ["Open", "Closed", "On Hold"])
            submit = st.form_submit_button("Save Manpower Plan", width="stretch")
            if submit:
                execute(
                    "INSERT INTO manpower(department, position, required, available, priority, status) VALUES (?, ?, ?, ?, ?, ?)",
                    (department, position, int(required), int(available), priority, status),
                )
                st.success("Manpower plan saved.")
                st.rerun()

    df = fetch_df("SELECT *, (required - available) AS gap FROM manpower")
    section("Manpower Gap Analysis")
    if df.empty:
        st.info("No manpower data available yet.")
    else:
        total_required = int(pd.to_numeric(df["required"], errors="coerce").fillna(0).sum())
        total_available = int(pd.to_numeric(df["available"], errors="coerce").fillna(0).sum())
        total_gap = int(pd.to_numeric(df["gap"], errors="coerce").fillna(0).clip(lower=0).sum())
        c1, c2, c3 = st.columns(3)
        c1.metric("Required", total_required)
        c2.metric("Available", total_available)
        c3.metric("Open Gap", total_gap)
        fig = px.bar(df, x="position", y="gap", color="priority", text="gap", hover_data=["department", "required", "available", "status"])
        fig.update_layout(height=380, xaxis_title="Position", yaxis_title="Gap")
        st.plotly_chart(fig, width="stretch")

    editable_table("manpower", "Manpower Planning Table", "manpower_table")

