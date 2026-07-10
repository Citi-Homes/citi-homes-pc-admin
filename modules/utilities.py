from __future__ import annotations

import streamlit as st

from config import BILL_STATUS
from database import execute, fetch_df
from modules.components import editable_table, format_currency, hero, section, status_badge

UTILITIES = ["Electricity", "Water", "Internet", "Telephone", "Waste Management", "Maintenance", "Other"]


def show() -> None:
    hero("Utility Bill Tracker", "Management reminder system for electricity, water, internet, telephone, maintenance and vendor bills.")

    with st.expander("Add Utility Bill", expanded=True):
        with st.form("utility_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            utility = c1.selectbox("Utility", UTILITIES)
            vendor = c2.text_input("Vendor")
            invoice_date = c3.date_input("Invoice Date")
            due_date = c1.date_input("Due Date")
            amount = c2.number_input("Amount AED", min_value=0.0, step=50.0)
            status = c3.selectbox("Status", BILL_STATUS)
            reminder_sent = c1.selectbox("Reminder Sent", ["No", "Yes"])
            submit = st.form_submit_button("Save Utility Bill", width="stretch")
            if submit:
                execute(
                    "INSERT INTO utilities(utility, vendor, invoice_date, due_date, amount, status, reminder_sent) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (utility, vendor, str(invoice_date), str(due_date), float(amount), status, reminder_sent),
                )
                st.success("Utility bill saved.")
                st.rerun()

    df = fetch_df("SELECT * FROM utilities")
    section("Utility Bill Status")
    if df.empty:
        st.info("No utility bills yet.")
    else:
        pending = df[df["status"].isin(["Pending", "Submitted"])]
        c1, c2, c3 = st.columns(3)
        c1.metric("Pending / Submitted", len(pending))
        c2.metric("Pending Amount", format_currency(pending["amount"].sum() if not pending.empty else 0))
        c3.metric("Total Bills", len(df))
        for _, r in pending.iterrows():
            st.markdown(
                f"<div class='card'><b>{r['utility']}</b> - {r['vendor']} - Due: {r['due_date']} - {format_currency(r['amount'])}<br>{status_badge(r['status'])}</div>",
                unsafe_allow_html=True,
            )

    editable_table("utilities", "Utility Tracker Table", "utilities_table")

