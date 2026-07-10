from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

from database import fetch_df
from modules.attendance_supabase import attendance_summary, fetch_attendance_records
from modules.components import format_currency, hero, section


def show() -> None:
    hero("Monthly P&C Report Generator", "Management-ready People & Culture and administration report covering workforce, recruitment, attendance, costs and pending issues.")

    month = st.text_input("Report Month", value="July 2026")

    employees = fetch_df("SELECT * FROM employees")
    recruitment = fetch_df("SELECT * FROM recruitment")
    try:
        attendance = fetch_attendance_records()
        attendance_stats = attendance_summary(attendance)
    except Exception:
        attendance = fetch_df("SELECT * FROM attendance")
        attendance_stats = {"records": 0, "checkins_today": 0, "total_hours": 0, "missing_punchouts": 0}
    pantry = fetch_df("SELECT * FROM pantry")
    utilities = fetch_df("SELECT * FROM utilities")
    documents = fetch_df("SELECT * FROM documents")

    opening_headcount = max(len(employees) - int((recruitment["status"] == "Joined").sum()) if not recruitment.empty else len(employees), 0)
    new_joiners = int((recruitment["status"] == "Joined").sum()) if not recruitment.empty else 0
    resignations = int((employees["status"].isin(["Resigned", "Terminated"])).sum()) if not employees.empty else 0
    closing_headcount = int((employees["status"] == "Active").sum()) if not employees.empty and "status" in employees else len(employees)
    cv_received = len(recruitment)
    active_pipeline = int(recruitment["status"].isin(["Applied", "Screening", "Shortlisted", "Interview Scheduled", "Selected", "Offer Sent"]).sum()) if not recruitment.empty else 0
    interviews = int(recruitment["status"].isin(["Interview Scheduled", "Selected", "Offer Sent", "Joined"]).sum()) if not recruitment.empty else 0
    selected = int(recruitment["status"].isin(["Selected", "Offer Sent", "Joined"]).sum()) if not recruitment.empty else 0
    joined = new_joiners
    overtime = 0
    if not attendance.empty and "hours" in attendance:
        overtime = (
            attendance.groupby(["emp_code", "record_date"])["hours"]
            .sum()
            .sub(8)
            .clip(lower=0)
            .sum()
        )
    pantry_expenses = pd.to_numeric(pantry.get("cost", pd.Series(dtype=float)), errors="coerce").fillna(0).sum() if not pantry.empty else 0
    utility_expenses = pd.to_numeric(utilities.get("amount", pd.Series(dtype=float)), errors="coerce").fillna(0).sum() if not utilities.empty else 0
    pending_docs = int(documents["status"].isin(["Expired", "Expiring Soon"]).sum()) if not documents.empty else 0
    pending_bills = int(utilities["status"].isin(["Pending", "Submitted"]).sum()) if not utilities.empty else 0

    report_rows = [
        ("Workforce", "Opening Headcount", opening_headcount),
        ("Workforce", "New Joiners", new_joiners),
        ("Workforce", "Resignations", resignations),
        ("Workforce", "Closing Headcount", closing_headcount),
        ("Recruitment", "Active Pipeline", active_pipeline),
        ("Recruitment", "CV Received", cv_received),
        ("Recruitment", "Interviews", interviews),
        ("Recruitment", "Selected", selected),
        ("Recruitment", "Joined", joined),
        ("Attendance", "Attendance Records", attendance_stats["records"]),
        ("Attendance", "Check-ins Today", attendance_stats["checkins_today"]),
        ("Attendance", "Total Hours", f'{attendance_stats["total_hours"]:,.2f}'),
        ("Attendance", "Overtime Hours", f"{float(overtime):,.2f}"),
        ("Administration", "Pantry Expenses", format_currency(pantry_expenses)),
        ("Administration", "Utility Expenses", format_currency(utility_expenses)),
        ("Administration", "Pending Documents", pending_docs),
        ("Administration", "Pending Bills", pending_bills),
    ]
    report_df = pd.DataFrame(report_rows, columns=["Section", "Metric", "Value"])

    section(f"Management Report - {month}")
    st.dataframe(report_df, width="stretch", hide_index=True)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        report_df.to_excel(writer, index=False, sheet_name="Monthly P&C Report")
        employees.to_excel(writer, index=False, sheet_name="Employees")
        recruitment.to_excel(writer, index=False, sheet_name="Recruitment")
        attendance.to_excel(writer, index=False, sheet_name="Attendance")
        pantry.to_excel(writer, index=False, sheet_name="Pantry")
        utilities.to_excel(writer, index=False, sheet_name="Utilities")
    st.download_button(
        "Download Management Report Excel",
        data=output.getvalue(),
        file_name=f"Citi_Homes_PC_Admin_Report_{month.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )

