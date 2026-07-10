from __future__ import annotations

from datetime import timedelta

import streamlit as st

from database import execute, fetch_df, update_document_statuses
from modules.components import editable_table, hero, section, status_badge

DOCUMENT_TYPES = ["Passport", "Emirates ID", "Visa", "Labour Contract", "Insurance", "Medical", "Other"]


def show() -> None:
    update_document_statuses()
    hero("Visa & Document Expiry Tracker", "UAE compliance control for passport, Emirates ID, visa, labour contract and insurance expiry alerts.")

    with st.expander("Add Document Record", expanded=True):
        with st.form("document_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            employee = c1.text_input("Employee")
            document = c2.selectbox("Document", DOCUMENT_TYPES)
            expiry_date = c3.date_input("Expiry Date")
            reminder_date = expiry_date - timedelta(days=30)
            c1.info(f"Reminder Date: {reminder_date}")
            submit = st.form_submit_button("Save Document", width="stretch")
            if submit:
                if not employee:
                    st.error("Employee name is required.")
                else:
                    execute(
                        "INSERT INTO documents(employee, document, expiry_date, reminder_date, status) VALUES (?, ?, ?, ?, ?)",
                        (employee, document, str(expiry_date), str(reminder_date), "Valid"),
                    )
                    update_document_statuses()
                    st.success("Document record saved.")
                    st.rerun()

    df = fetch_df("SELECT * FROM documents")
    section("Compliance Alerts")
    if df.empty:
        st.info("No document records yet.")
    else:
        expired = int((df["status"] == "Expired").sum())
        soon = int((df["status"] == "Expiring Soon").sum())
        valid = int((df["status"] == "Valid").sum())
        c1, c2, c3 = st.columns(3)
        c1.metric("Expired", expired)
        c2.metric("Within 30 Days", soon)
        c3.metric("Valid", valid)
        alerts = df[df["status"].isin(["Expired", "Expiring Soon"])]
        if not alerts.empty:
            for _, r in alerts.iterrows():
                st.markdown(
                    f"<div class='card'><b>{r['employee']}</b> - {r['document']} - Expiry: {r['expiry_date']}<br>{status_badge(r['status'])}</div>",
                    unsafe_allow_html=True,
                )

    editable_table("documents", "Document Expiry Table", "documents_table")

