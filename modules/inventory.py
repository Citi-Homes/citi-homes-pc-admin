from __future__ import annotations

import streamlit as st

from database import execute, fetch_df
from modules.components import editable_table, hero, section

CATEGORIES = ["Laptop", "Printer", "Furniture", "Stationery", "PPE", "Tools", "Office Equipment", "Other"]
CONDITION = ["New", "Good", "Needs Repair", "Damaged", "Disposed"]


def show() -> None:
    hero("Office Inventory", "Administration control for laptops, printers, furniture, stationery, PPE, tools and office assets.")

    with st.expander("Add Inventory Item", expanded=True):
        with st.form("inventory_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            item = c1.text_input("Item")
            category = c2.selectbox("Category", CATEGORIES)
            quantity = c3.number_input("Quantity", min_value=0, step=1)
            location = c1.text_input("Location")
            responsible_person = c2.text_input("Responsible Person")
            condition = c3.selectbox("Condition", CONDITION)
            submit = st.form_submit_button("Save Inventory", width="stretch")
            if submit:
                if not item:
                    st.error("Item name is required.")
                else:
                    execute(
                        "INSERT INTO inventory(item, category, quantity, location, responsible_person, condition) VALUES (?, ?, ?, ?, ?, ?)",
                        (item, category, int(quantity), location, responsible_person, condition),
                    )
                    st.success("Inventory item saved.")
                    st.rerun()

    df = fetch_df("SELECT * FROM inventory")
    section("Inventory Summary")
    if df.empty:
        st.info("No inventory records yet.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Items", int(df["quantity"].sum()))
        c2.metric("Categories", df["category"].nunique())
        c3.metric("Needs Attention", int(df["condition"].isin(["Needs Repair", "Damaged"]).sum()))
        st.dataframe(df, width="stretch", hide_index=True)

    editable_table("inventory", "Office Inventory Table", "inventory_table")

