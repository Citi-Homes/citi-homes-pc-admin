from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from config import DESIGNATIONS, RECRUITMENT_STATUS
from database import execute, fetch_df, reset_table
from modules.components import download_excel_button, hero, section, show_kpis
from modules.page_import import import_panel


PIPELINE_TABS = {
    "All": RECRUITMENT_STATUS,
    "New": ["Applied", "Screening"],
    "Shortlisted": ["Shortlisted"],
    "Interview": ["Interview Scheduled", "Selected"],
    "Offer": ["Offer Sent"],
    "Joined": ["Joined"],
    "Closed": ["Rejected", "Hold"],
}


def _display_recruitment(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "candidate",
        "position",
        "source",
        "mobile",
        "location",
        "gcc_experience",
        "total_experience",
        "current_salary",
        "expected_salary",
        "notice_period",
        "interview_date",
        "status",
    ]
    if df.empty:
        return pd.DataFrame(columns=[col.replace("_", " ").title() for col in columns])

    visible = df[[col for col in columns if col in df.columns]].copy()
    visible.columns = [col.replace("_", " ").title() for col in visible.columns]
    return visible


def _count_status(df: pd.DataFrame, statuses: list[str]) -> int:
    if df.empty or "status" not in df.columns:
        return 0
    return int(df["status"].isin(statuses).sum())


def _dashboard(df: pd.DataFrame) -> None:
    section("Recruitment Dashboard")

    total = len(df)
    interviews = _count_status(df, ["Interview Scheduled", "Selected", "Offer Sent", "Joined"])
    offers = _count_status(df, ["Offer Sent", "Joined"])
    joined = _count_status(df, ["Joined"])
    active = _count_status(df, ["Applied", "Screening", "Shortlisted", "Interview Scheduled", "Selected", "Offer Sent"])
    conversion = f"{(joined / total * 100):.0f}%" if total else "0%"

    show_kpis(
        [
            ("CV Received", total, "Total candidate records"),
            ("Active Pipeline", active, "Open recruitment cases"),
            ("Interviews", interviews, "Interviewed / scheduled"),
            ("Joined", joined, f"Conversion {conversion}"),
        ],
        cols=4,
    )

    if df.empty:
        st.info("No candidates recorded yet.")
        return

    c1, c2 = st.columns([1.1, 1])
    with c1:
        status_df = df["status"].value_counts().reindex(RECRUITMENT_STATUS).fillna(0).reset_index()
        status_df.columns = ["Status", "Candidates"]
        fig = px.bar(status_df, x="Status", y="Candidates", text="Candidates")
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, width="stretch")

    with c2:
        source_df = df["source"].fillna("Unassigned").replace("", "Unassigned").value_counts().reset_index()
        source_df.columns = ["Source", "Candidates"]
        fig = px.pie(source_df, names="Source", values="Candidates", hole=0.52)
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, width="stretch")


def _pipeline_tabs(df: pd.DataFrame) -> None:
    section("Recruitment Pipeline")
    tabs = st.tabs(list(PIPELINE_TABS.keys()))

    for tab, (label, statuses) in zip(tabs, PIPELINE_TABS.items()):
        with tab:
            filtered = df[df["status"].isin(statuses)] if not df.empty and "status" in df.columns else df
            st.dataframe(_display_recruitment(filtered), hide_index=True, width="stretch")


def _add_candidate_form() -> None:
    section("Add Candidate")
    with st.form("candidate_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        candidate = c1.text_input("Candidate Name")
        position = c2.selectbox("Position", DESIGNATIONS)
        source = c3.selectbox("Source", ["LinkedIn", "WhatsApp Group", "Referral", "Indeed", "Walk-in", "Agency", "Other"])
        mobile = c1.text_input("Mobile")
        location = c2.text_input("Location", placeholder="UAE / Pakistan / India")
        gcc_experience = c3.number_input("GCC Experience", min_value=0.0, step=0.5)
        total_experience = c1.number_input("Total Experience", min_value=0.0, step=0.5)
        current_salary = c2.number_input("Current Salary", min_value=0.0, step=100.0)
        expected_salary = c3.number_input("Expected Salary", min_value=0.0, step=100.0)
        notice_period = c1.text_input("Notice Period")
        interview_date = c2.date_input("Interview Date", value=date.today())
        status = c3.selectbox("Status", RECRUITMENT_STATUS)
        submit = st.form_submit_button("Save Candidate", width="stretch")

        if submit:
            if not candidate:
                st.error("Candidate name is required.")
                return

            execute(
                """
                INSERT INTO recruitment(candidate, position, source, mobile, location, gcc_experience, total_experience, current_salary, expected_salary, notice_period, interview_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (candidate, position, source, mobile, location, gcc_experience, total_experience, current_salary, expected_salary, notice_period, str(interview_date), status),
            )
            st.success("Candidate saved.")
            st.rerun()


def _recruitment_table() -> None:
    section("Recruitment Tracker Table")
    df = fetch_df("SELECT * FROM recruitment ORDER BY id ASC")
    table_df = df.copy()
    table_df.insert(0, "Sr. No", range(1, len(table_df) + 1))
    edited = st.data_editor(
        table_df,
        width="stretch",
        hide_index=True,
        num_rows="dynamic",
        disabled=["Sr. No", "id"],
        column_config={
            "id": None,
            "Sr. No": st.column_config.NumberColumn("Sr. No", width="small"),
        },
        key="recruitment_table",
    )
    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("Save Changes", key="save_recruitment_table", width="stretch"):
            reset_table("recruitment", edited)
            st.success("Changes saved successfully.")
            st.rerun()
    with c2:
        export_df = edited.drop(columns=["id"], errors="ignore")
        download_excel_button(export_df, "recruitment.xlsx", "Export this table")


def show() -> None:
    hero("Recruitment Tracker", "Control hiring pipeline, source tracking, salary expectations, interview dates and final joining status.")

    df = fetch_df("SELECT * FROM recruitment")
    _dashboard(df)
    _pipeline_tabs(df)
    _recruitment_table()
    import_panel("recruitment", "Import Recruitment Data")
    _add_candidate_form()
