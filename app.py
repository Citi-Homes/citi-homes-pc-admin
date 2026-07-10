from __future__ import annotations

import streamlit as st

from config import APP_NAME, APP_VERSION, COMPANY_NAME
from database import create_tables
from modules.auth import microsoft_login_enabled, require_microsoft_user
from modules.components import load_css
from modules import (
    attendance,
    data_import,
    dashboard,
    documents,
    employees,
    interview,
    inventory,
    joining,
    leave,
    microsoft_lists_admin,
    pantry,
    recruitment,
    reports,
    supabase_admin,
    tasks,
    utilities,
    vendors,
)
from database import authenticate

st.set_page_config(
    page_title=APP_NAME,
    page_icon=":material/apartment:",
    layout="wide",
    initial_sidebar_state="expanded",
)

create_tables()
load_css()


def login_screen() -> None:
    microsoft_user = require_microsoft_user()
    if microsoft_user:
        st.session_state["user"] = microsoft_user
        st.rerun()

    st.markdown(
        """
        <div class="login-shell">
            <div class="login-logo brand-mark"><span>CH</span></div>
            <div class="login-box">
                <h1>CITI HOMES</h1>
                <h3>P&C Administration System</h3>
                <p>Secure management dashboard for Operations, recruitment, attendance, procurement and administration control.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1, 1.1, 1])
    with c2:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="admin123")
            submitted = st.form_submit_button("Login", width="stretch")
            if submitted:
                user = authenticate(username, password)
                if user:
                    st.session_state["user"] = user
                    st.success("Login successful.")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        st.info("Default login: admin / admin123. Management view: management / management123. Change these before live use.")


def sidebar() -> str:
    user = st.session_state.get("user", {})
    st.sidebar.markdown(
        f"""
        <div class="brand-lockup">
            <div class="brand-mark"><span>CH</span></div>
            <div>
                <div class="brand-name">{COMPANY_NAME}</div>
                <div class="brand-subtitle">A Citi Developers company</div>
            </div>
        </div>
        <div class="brand-chip">P&C Administration System</div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Logged in as: {user.get('full_name', 'User')}")
    st.sidebar.caption(f"Role: {user.get('role', 'Admin')}")
    st.sidebar.markdown("---")

    if user.get("role") == "Management":
        pages = ["Dashboard", "Monthly P&C Report"]
    else:
        pages = [
            "Dashboard",
            "Employee Master",
            "Recruitment Tracker",
            "Interview Evaluation",
            "Joining Checklist",
            "Attendance Portal",
            "Leave Management",
            "Visa & Documents",
            "Pantry Management",
            "Utility Bills",
            "Office Inventory",
            "Vendor Database",
            "Monthly P&C Report",
            "P&C Task Calendar",
        ]
        if user.get("role") == "Admin":
            pages.extend(["Excel Data Import", "Supabase Setup", "Microsoft Lists Setup"])

    selected = st.sidebar.radio("Navigation", pages, label_visibility="collapsed")
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", width="stretch"):
        st.session_state.clear()
        if microsoft_login_enabled() and st.user.is_logged_in:
            st.logout()
        st.rerun()
    st.sidebar.caption(f"Version {APP_VERSION}")
    return selected


def main() -> None:
    microsoft_user = require_microsoft_user()
    if microsoft_user:
        st.session_state["user"] = microsoft_user

    if "user" not in st.session_state:
        login_screen()
        return

    page = sidebar()

    if page == "Dashboard":
        dashboard.show()
    elif page == "Excel Data Import":
        data_import.show()
    elif page == "Employee Master":
        employees.show()
    elif page == "Recruitment Tracker":
        recruitment.show()
    elif page == "Interview Evaluation":
        interview.show()
    elif page == "Joining Checklist":
        joining.show()
    elif page == "Attendance Portal":
        attendance.show()
    elif page == "Leave Management":
        leave.show()
    elif page == "Visa & Documents":
        documents.show()
    elif page == "Pantry Management":
        pantry.show()
    elif page == "Utility Bills":
        utilities.show()
    elif page == "Office Inventory":
        inventory.show()
    elif page == "Vendor Database":
        vendors.show()
    elif page == "Monthly P&C Report":
        reports.show()
    elif page == "P&C Task Calendar":
        tasks.show()
    elif page == "Microsoft Lists Setup":
        microsoft_lists_admin.show()
    elif page == "Supabase Setup":
        supabase_admin.show()


if __name__ == "__main__":
    main()

