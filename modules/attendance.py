from __future__ import annotations

from datetime import date

import plotly.express as px
import streamlit as st

from config import ATTENDANCE_PORTAL_URL
from modules.attendance_supabase import (
    attendance_summary,
    display_records,
    fetch_attendance_records,
    hours_by_employee,
)
from modules.components import hero, section, show_kpis


def _load_records():
    return fetch_attendance_records()


def show() -> None:
    hero(
        "Attendance Portal",
        "Live attendance data is connected directly from the Citi Homes Supabase attendance system.",
    )

    launch_url = ATTENDANCE_PORTAL_URL

    c1, c2, c3 = st.columns([1, 1, 3])
    with c1:
        st.link_button("Open portal", launch_url, width="stretch")
    with c2:
        if st.button("Refresh data", width="stretch"):
            st.rerun()
    with c3:
        st.caption("Attendance details below are read live from Supabase. The embedded portal remains available for punch-in/out operations.")

    try:
        records = _load_records()
    except Exception:
        st.warning("Live attendance data is not reachable from this local session. You can still use the attendance portal below.")
        section("Portal fallback")
        st.iframe(launch_url, height=820)
        return

    summary = attendance_summary(records)
    section("Live attendance summary")
    show_kpis(
        [
            ("Employees", summary["employees"], "Registered in attendance portal"),
            ("Check-ins Today", summary["checkins_today"], "Live records for today"),
            ("Total Records", summary["records"], "All Supabase attendance rows"),
            ("Total Hours", f'{summary["total_hours"]:,.2f}', "Logged working hours"),
        ],
        cols=4,
    )

    tab_overview, tab_records, tab_hours, tab_portal = st.tabs(["Overview", "All records", "Hours report", "Portal"])

    with tab_overview:
        c1, c2 = st.columns([1.1, 1])
        with c1:
            section("Today's check-ins")
            today_records = records[records["record_date"] == date.today().isoformat()] if not records.empty else records
            st.dataframe(display_records(today_records).head(20), hide_index=True, width="stretch")
        with c2:
            section("Category breakdown")
            if records.empty or "category" not in records:
                st.info("No category data available.")
            else:
                category_counts = records["category"].fillna("Unassigned").value_counts().reset_index()
                category_counts.columns = ["Category", "Records"]
                fig = px.pie(category_counts, names="Category", values="Records", hole=0.48)
                fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, width="stretch")

    with tab_records:
        section("All attendance records")
        st.dataframe(display_records(records), hide_index=True, width="stretch")
        st.download_button(
            "Download attendance CSV",
            data=display_records(records).to_csv(index=False).encode("utf-8"),
            file_name="citi_homes_attendance_records.csv",
            mime="text/csv",
            width="stretch",
        )

    with tab_hours:
        section("Hours by employee")
        hours = hours_by_employee(records)
        st.dataframe(hours, hide_index=True, width="stretch")
        st.download_button(
            "Download hours report CSV",
            data=hours.to_csv(index=False).encode("utf-8"),
            file_name="citi_homes_attendance_hours.csv",
            mime="text/csv",
            width="stretch",
        )

    with tab_portal:
        section("Live attendance portal")
        st.iframe(launch_url, height=820)
