from __future__ import annotations

import streamlit as st

from config import TASK_STATUS
from database import execute, fetch_df
from modules.components import editable_table, hero, section, status_badge

FREQUENCY = ["Daily", "Weekly", "Monthly", "Quarterly", "Yearly", "One-time"]


def show() -> None:
    hero("P&C Task Calendar", "Personal control calendar for recurring People & Culture and administration responsibilities.")

    with st.expander("Add P&C/Admin Task", expanded=True):
        with st.form("task_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            task = c1.text_input("Task")
            frequency = c2.selectbox("Frequency", FREQUENCY)
            due_date = c3.text_input("Due Date", placeholder="3rd of every month / Every Friday")
            status = c1.selectbox("Status", TASK_STATUS)
            remarks = st.text_area("Remarks")
            submit = st.form_submit_button("Save Task", width="stretch")
            if submit:
                if not task:
                    st.error("Task name is required.")
                else:
                    execute(
                        "INSERT INTO tasks(task, frequency, due_date, status, remarks) VALUES (?, ?, ?, ?, ?)",
                        (task, frequency, due_date, status, remarks),
                    )
                    st.success("Task saved.")
                    st.rerun()

    df = fetch_df("SELECT * FROM tasks")
    section("Task Control")
    if df.empty:
        st.info("No tasks yet.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Tasks", len(df))
        c2.metric("Pending", int((df["status"] == "Pending").sum()))
        c3.metric("Completed", int((df["status"] == "Completed").sum()))
        for _, r in df.iterrows():
            st.markdown(
                f"<div class='card'><b>{r['task']}</b> - {r['frequency']} - Due: {r['due_date']}<br>{status_badge(r['status'])}<br><span class='small-muted'>{r['remarks'] or ''}</span></div>",
                unsafe_allow_html=True,
            )

    editable_table("tasks", "P&C Task Calendar Table", "tasks_table")

