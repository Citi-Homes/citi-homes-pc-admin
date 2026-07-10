from __future__ import annotations

import streamlit as st

from database import execute, fetch_df
from modules.components import editable_table, hero, section
from modules.page_import import import_panel

SERVICES = ["Security", "Cleaning", "Transport", "Accommodation", "Maintenance", "IT", "Pest Control", "Waste Management", "Other"]
CONTRACT_STATUS = ["Active", "Under Review", "Expired", "Not Started", "Terminated"]


def show() -> None:
    hero("Vendor Contact Database", "Vendor control for security, cleaning, transport, accommodation, maintenance and administration services.")

    with st.expander("Add Vendor", expanded=True):
        with st.form("vendor_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            vendor = c1.text_input("Vendor")
            service = c2.selectbox("Service", SERVICES)
            contact_person = c3.text_input("Contact Person")
            mobile = c1.text_input("Mobile")
            contract_status = c2.selectbox("Contract Status", CONTRACT_STATUS)
            renewal_date = c3.date_input("Renewal Date")
            submit = st.form_submit_button("Save Vendor", width="stretch")
            if submit:
                if not vendor:
                    st.error("Vendor name is required.")
                else:
                    execute(
                        "INSERT INTO vendors(vendor, service, contact_person, mobile, contract_status, renewal_date) VALUES (?, ?, ?, ?, ?, ?)",
                        (vendor, service, contact_person, mobile, contract_status, str(renewal_date)),
                    )
                    st.success("Vendor saved.")
                    st.rerun()

    df = fetch_df("SELECT * FROM vendors")
    section("Vendor Summary")
    if df.empty:
        st.info("No vendor records yet.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Vendors", len(df))
        c2.metric("Active Contracts", int((df["contract_status"] == "Active").sum()))
        c3.metric("Under Review", int((df["contract_status"] == "Under Review").sum()))
        st.dataframe(df, width="stretch", hide_index=True)

    editable_table("vendors", "Vendor Database Table", "vendors_table")
    import_panel("vendors", "Import Vendor Data")

