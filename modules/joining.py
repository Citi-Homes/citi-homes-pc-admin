from __future__ import annotations

import streamlit as st

from config import CHECKLIST_STATUS
from database import execute, fetch_df
from modules.components import editable_table, hero, section

CHECKS = ["offer_letter", "passport_copy", "visa", "emirates_id", "medical", "contract", "insurance", "bank_details"]


def calc_completed_pct(values: list[str]) -> float:
    applicable = [v for v in values if v != "Not Applicable"]
    if not applicable:
        return 100.0
    completed = sum(1 for v in applicable if v == "Received")
    return round((completed / len(applicable)) * 100, 2)


def show() -> None:
    hero("Joining Checklist", "Standardized onboarding control for offer letter, visa, contract, insurance, bank details and documents.")

    with st.expander("Add Joining Checklist", expanded=True):
        with st.form("joining_form", clear_on_submit=True):
            employee = st.text_input("Employee / Candidate Name")
            c1, c2, c3, c4 = st.columns(4)
            vals = {
                "offer_letter": c1.selectbox("Offer Letter", CHECKLIST_STATUS),
                "passport_copy": c2.selectbox("Passport Copy", CHECKLIST_STATUS),
                "visa": c3.selectbox("Visa", CHECKLIST_STATUS),
                "emirates_id": c4.selectbox("Emirates ID", CHECKLIST_STATUS),
                "medical": c1.selectbox("Medical", CHECKLIST_STATUS),
                "contract": c2.selectbox("Contract", CHECKLIST_STATUS),
                "insurance": c3.selectbox("Insurance", CHECKLIST_STATUS),
                "bank_details": c4.selectbox("Bank Details", CHECKLIST_STATUS),
            }
            submit = st.form_submit_button("Save Checklist", width="stretch")
            if submit:
                if not employee:
                    st.error("Employee name is required.")
                else:
                    pct = calc_completed_pct(list(vals.values()))
                    execute(
                        """
                        INSERT INTO joining_checklist(employee, offer_letter, passport_copy, visa, emirates_id, medical, contract, insurance, bank_details, completed_pct)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (employee, vals["offer_letter"], vals["passport_copy"], vals["visa"], vals["emirates_id"], vals["medical"], vals["contract"], vals["insurance"], vals["bank_details"], pct),
                    )
                    st.success("Joining checklist saved.")
                    st.rerun()

    df = fetch_df("SELECT * FROM joining_checklist")
    section("Onboarding Progress")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Joining Files", len(df))
        c2.metric("Average Completion", f"{df['completed_pct'].mean():.1f}%")
        c3.metric("Fully Completed", int((df["completed_pct"] >= 100).sum()))
        for _, row in df.iterrows():
            st.progress(float(row["completed_pct"]) / 100, text=f"{row['employee']} - {row['completed_pct']:.0f}% completed")
    else:
        st.info("No joining checklist records yet.")

    editable_table("joining_checklist", "Joining Checklist Table", "joining_table")

