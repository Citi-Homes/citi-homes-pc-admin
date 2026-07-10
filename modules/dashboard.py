from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from database import fetch_df, update_document_statuses
from modules.attendance_supabase import attendance_summary, fetch_attendance_records
from modules.components import format_currency, hero, section, show_kpis, safe_sum, status_badge


def _count_status(df: pd.DataFrame, statuses: list[str]) -> int:
    if df.empty or "status" not in df.columns:
        return 0
    return int(df["status"].isin(statuses).sum())


def show() -> None:
    update_document_statuses()
    current_month = datetime.now().strftime("%B %Y")
    hero("CITI HOMES P&C & ADMIN DASHBOARD", f"Management View - Month: {current_month}")

    employees = fetch_df("SELECT * FROM employees")
    recruitment = fetch_df("SELECT * FROM recruitment")
    documents = fetch_df("SELECT * FROM documents")
    pantry = fetch_df("SELECT * FROM pantry")
    utilities = fetch_df("SELECT * FROM utilities")
    try:
        attendance_live = fetch_attendance_records()
        attendance_stats = attendance_summary(attendance_live)
    except Exception:
        attendance_live = pd.DataFrame()
        attendance_stats = {"checkins_today": 0, "total_hours": 0}

    total_employees = int((employees["status"].eq("Active")).sum()) if not employees.empty and "status" in employees else len(employees)
    cv_received = len(recruitment)
    active_pipeline = _count_status(recruitment, ["Applied", "Screening", "Shortlisted", "Interview Scheduled", "Selected", "Offer Sent"])
    interviewed = _count_status(recruitment, ["Interview Scheduled", "Selected", "Offer Sent", "Joined"])
    offers = _count_status(recruitment, ["Offer Sent", "Joined"])
    joined = _count_status(recruitment, ["Joined"])
    pending_docs = _count_status(documents, ["Expired", "Expiring Soon"])
    pantry_cost = safe_sum(pantry, "cost")
    pending_bills = _count_status(utilities, ["Pending", "Submitted"])
    pending_visa = int((employees["visa_status"].isin(["Processing", "Not Started", "On Hold", "Renewal"])).sum()) if not employees.empty and "visa_status" in employees else 0

    section("Workforce Summary")
    show_kpis(
        [
            ("Total Employees", total_employees, "Active headcount"),
            ("Active Pipeline", active_pipeline, "Open recruitment cases"),
            ("New Joiners", max(joined, 0), "Joined from recruitment pipeline"),
            ("Pending Visa", pending_visa, "Processing / not started / hold"),
        ],
        cols=4,
    )

    section("Recruitment")
    show_kpis(
        [
            ("CV Received", cv_received, "Total candidate records"),
            ("Interviewed", interviewed, "Scheduled or completed"),
            ("Offers Released", offers, "Offer Sent + Joined"),
            ("Joined", joined, "Successfully onboarded"),
        ],
        cols=4,
    )

    section("Administration")
    show_kpis(
        [
            ("Pantry Cost", format_currency(pantry_cost), "Current tracker total"),
            ("Pending Bills", pending_bills, "Pending + submitted"),
            ("Documents Expiring", pending_docs, "Expired or within 30 days"),
            ("Check-ins Today", attendance_stats["checkins_today"], "Live Supabase attendance"),
        ],
        cols=4,
    )

    c1, c2 = st.columns([1.1, 1])
    with c1:
        section("Recruitment Funnel")
        if recruitment.empty:
            st.info("Recruitment tracker has no records yet.")
        else:
            order = ["Applied", "Screening", "Shortlisted", "Interview Scheduled", "Selected", "Offer Sent", "Joined", "Rejected", "Hold"]
            counts = recruitment["status"].value_counts().reindex(order).fillna(0).reset_index()
            counts.columns = ["Status", "Candidates"]
            fig = px.bar(counts, x="Status", y="Candidates", text="Candidates")
            fig.update_layout(height=380, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="", yaxis_title="Candidates")
            st.plotly_chart(fig, width="stretch")

    with c2:
        section("Recruitment Sources")
        if recruitment.empty or "source" not in recruitment.columns:
            st.info("Recruitment tracker has no source data yet.")
        else:
            sources = recruitment["source"].fillna("Unassigned").replace("", "Unassigned").value_counts().reset_index()
            sources.columns = ["Source", "Candidates"]
            fig = px.pie(sources, names="Source", values="Candidates", hole=0.48)
            fig.update_layout(height=380, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, width="stretch")

    c3, c4 = st.columns([1, 1])
    with c3:
        section("Document Alerts")
        alerts = documents[documents["status"].isin(["Expired", "Expiring Soon"])] if not documents.empty else pd.DataFrame()
        if alerts.empty:
            st.success("No expired or expiring documents found.")
        else:
            for _, r in alerts.head(8).iterrows():
                st.markdown(
                    f"<div class='card'><b>{r['employee']}</b> - {r['document']} - Expiry: {r['expiry_date']}<br>{status_badge(r['status'])}</div>",
                    unsafe_allow_html=True,
                )

    with c4:
        section("Pending Admin Bills")
        pending = utilities[utilities["status"].isin(["Pending", "Submitted"])] if not utilities.empty else pd.DataFrame()
        if pending.empty:
            st.success("No pending utility bills.")
        else:
            for _, r in pending.head(8).iterrows():
                st.markdown(
                    f"<div class='card'><b>{r['utility']}</b> - {r['vendor']}<br>Due: {r['due_date']} - Amount: {format_currency(r['amount'])}<br>{status_badge(r['status'])}</div>",
                    unsafe_allow_html=True,
                )


def _attendance_pct(attendance: pd.DataFrame) -> str:
    if attendance.empty:
        return "0%"
    present = pd.to_numeric(attendance.get("present", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    working = pd.to_numeric(attendance.get("working_days", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    if working <= 0:
        return "0%"
    return f"{(present / working) * 100:.1f}%"

