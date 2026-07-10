from __future__ import annotations

import streamlit as st

from config import DEPARTMENTS, DESIGNATIONS, EMPLOYMENT_TYPES, VISA_STATUS
from database import execute, fetch_df
from modules.components import editable_table, hero, section


def show() -> None:
    hero("Employee Master Database", "Central People & Culture database for Citi Homes employees, visa status, contact details and document references.")

    df = fetch_df("SELECT * FROM employees")

    section("Employee Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Employees", len(df))
    c2.metric("Active", int((df["status"] == "Active").sum()) if not df.empty else 0)
    c3.metric("Pending Visa", int(df["visa_status"].isin(["Processing", "Not Started", "On Hold", "Renewal"]).sum()) if not df.empty else 0)
    c4.metric("Departments", df["department"].nunique() if not df.empty else 0)

    editable_table("employees", "Employee Master Table", "employees_table")

    section("Add New Employee")
    with st.form("employee_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        employee_id = c1.text_input("Employee ID", placeholder="CH001")
        name = c2.text_input("Employee Name")
        department = c3.selectbox("Department", DEPARTMENTS)
        designation = c1.selectbox("Designation", DESIGNATIONS)
        nationality = c2.text_input("Nationality")
        joining_date = c3.date_input("Joining Date")
        employment_type = c1.selectbox("Employment Type", EMPLOYMENT_TYPES)
        visa_status = c2.selectbox("Visa Status", VISA_STATUS)
        status = c3.selectbox("Employee Status", ["Active", "Inactive", "Resigned", "Terminated"])
        emirates_id_expiry = c1.date_input("Emirates ID Expiry")
        passport_expiry = c2.date_input("Passport Expiry")
        mobile = c3.text_input("Mobile")
        emergency_contact = st.text_input("Emergency Contact")
        submit = st.form_submit_button("Save Employee", width="stretch")
        if submit:
            if not employee_id or not name:
                st.error("Employee ID and Employee Name are required.")
            else:
                try:
                    execute(
                        """
                        INSERT INTO employees(employee_id, name, department, designation, nationality, joining_date, employment_type, visa_status, emirates_id_expiry, passport_expiry, mobile, emergency_contact, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (employee_id, name, department, designation, nationality, str(joining_date), employment_type, visa_status, str(emirates_id_expiry), str(passport_expiry), mobile, emergency_contact, status),
                    )
                    st.success("Employee saved successfully.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not save employee: {exc}")

