from __future__ import annotations

import re
import shutil
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from config import DB_PATH
from database import fetch_df, reset_table, table_columns
from modules.components import hero, section


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).strip().lower())


TABLES: dict[str, dict[str, Any]] = {
    "employees": {
        "label": "Employee Master",
        "sheet_aliases": ["employees", "employee master", "employee", "staff"],
        "required": ["employee_id", "name", "department", "designation"],
        "defaults": {"status": "Active", "employment_type": "Employee", "visa_status": "Not Started"},
        "date_columns": ["joining_date", "emirates_id_expiry", "passport_expiry"],
        "aliases": {
            "employee_id": ["employee id", "emp id", "emp no", "code", "staff id"],
            "name": ["employee name", "full name", "staff name", "name"],
            "department": ["dept", "department"],
            "designation": ["position", "job title", "designation"],
            "nationality": ["nationality"],
            "joining_date": ["joining date", "join date", "date of joining", "doj"],
            "employment_type": ["employment type", "type"],
            "visa_status": ["visa status", "visa"],
            "emirates_id_expiry": ["emirates id expiry", "eid expiry", "emirates expiry"],
            "passport_expiry": ["passport expiry", "passport exp"],
            "mobile": ["mobile", "phone", "contact no", "contact number"],
            "emergency_contact": ["emergency contact"],
            "status": ["status", "employee status"],
        },
    },
    "manpower": {
        "label": "Manpower Planning",
        "sheet_aliases": ["manpower", "manpower planning", "open positions"],
        "required": ["department", "position"],
        "defaults": {"required": 0, "available": 0, "priority": "Medium", "status": "Open"},
        "numeric_columns": ["required", "available"],
        "aliases": {
            "department": ["department", "dept"],
            "position": ["position", "designation", "job title"],
            "required": ["required", "required manpower", "requirement", "planned"],
            "available": ["available", "current", "existing", "actual"],
            "priority": ["priority"],
            "status": ["status"],
        },
    },
    "recruitment": {
        "label": "Recruitment Tracker",
        "sheet_aliases": ["recruitment", "recruitment tracker", "candidates", "candidate"],
        "required": ["candidate", "position"],
        "defaults": {"status": "Applied", "gcc_experience": 0, "total_experience": 0, "current_salary": 0, "expected_salary": 0},
        "date_columns": ["interview_date"],
        "numeric_columns": ["gcc_experience", "total_experience", "current_salary", "expected_salary"],
        "aliases": {
            "candidate": ["candidate", "candidate name", "applicant", "name"],
            "position": ["position", "designation", "job title"],
            "source": ["source"],
            "mobile": ["mobile", "phone", "contact no", "contact number"],
            "location": ["location"],
            "gcc_experience": ["gcc experience", "gcc exp"],
            "total_experience": ["total experience", "total exp", "experience"],
            "current_salary": ["current salary"],
            "expected_salary": ["expected salary"],
            "notice_period": ["notice period"],
            "interview_date": ["interview date"],
            "status": ["status", "candidate status"],
        },
    },
    "interview_evaluation": {
        "label": "Interview Evaluation",
        "sheet_aliases": ["interview", "interview evaluation", "evaluation"],
        "required": ["candidate", "position"],
        "defaults": {"technical_score": 1, "experience_score": 1, "communication_score": 1},
        "date_columns": ["interview_date"],
        "numeric_columns": ["technical_score", "experience_score", "communication_score"],
        "aliases": {
            "candidate": ["candidate", "candidate name", "name"],
            "position": ["position", "designation"],
            "interview_date": ["interview date"],
            "technical_score": ["technical score", "technical"],
            "experience_score": ["experience score", "experience"],
            "communication_score": ["communication score", "communication"],
            "final_decision": ["final decision", "decision", "status"],
            "interviewer_comments": ["interviewer comments", "comments", "remarks"],
        },
    },
    "joining_checklist": {
        "label": "Joining Checklist",
        "sheet_aliases": ["joining", "joining checklist", "onboarding"],
        "required": ["employee"],
        "defaults": {"completed_pct": 0},
        "numeric_columns": ["completed_pct"],
        "aliases": {
            "employee": ["employee", "employee name", "name"],
            "offer_letter": ["offer letter"],
            "passport_copy": ["passport copy"],
            "visa": ["visa"],
            "emirates_id": ["emirates id", "eid"],
            "medical": ["medical"],
            "contract": ["contract"],
            "insurance": ["insurance"],
            "bank_details": ["bank details"],
            "completed_pct": ["completed pct", "completion", "completed %"],
        },
    },
    "attendance": {
        "label": "Attendance Portal",
        "sheet_aliases": ["attendance", "attendance portal", "attendance management"],
        "required": ["employee"],
        "defaults": {"working_days": 0, "present": 0, "absent": 0, "late": 0, "overtime": 0},
        "numeric_columns": ["working_days", "present", "absent", "late", "overtime"],
        "aliases": {
            "employee": ["employee", "employee name", "name"],
            "department": ["department", "dept"],
            "month": ["month", "period"],
            "working_days": ["working days", "work days"],
            "present": ["present"],
            "absent": ["absent"],
            "late": ["late", "late marks"],
            "overtime": ["overtime", "ot", "overtime hours"],
            "remarks": ["remarks", "comments"],
        },
    },
    "leave_management": {
        "label": "Leave Management",
        "sheet_aliases": ["leave", "leave management"],
        "required": ["employee", "leave_type"],
        "defaults": {"opening_balance": 0, "used": 0, "remaining": 0},
        "numeric_columns": ["opening_balance", "used", "remaining"],
        "aliases": {
            "employee": ["employee", "employee name", "name"],
            "leave_type": ["leave type", "type"],
            "opening_balance": ["opening balance", "opening"],
            "used": ["used", "taken"],
            "remaining": ["remaining", "balance"],
        },
    },
    "documents": {
        "label": "Visa & Documents",
        "sheet_aliases": ["documents", "visa documents", "visa & documents", "document tracker"],
        "required": ["employee", "document", "expiry_date"],
        "defaults": {"status": "Valid"},
        "date_columns": ["expiry_date", "reminder_date"],
        "aliases": {
            "employee": ["employee", "employee name", "name"],
            "document": ["document", "document type", "doc type"],
            "expiry_date": ["expiry date", "expiry", "expiration date"],
            "reminder_date": ["reminder date", "reminder"],
            "status": ["status"],
        },
    },
    "pantry": {
        "label": "Pantry Management",
        "sheet_aliases": ["pantry", "pantry management"],
        "required": ["item"],
        "defaults": {"opening": 0, "purchased": 0, "used": 0, "closing": 0, "required_next_month": 0, "cost": 0},
        "numeric_columns": ["opening", "purchased", "used", "closing", "required_next_month", "cost"],
        "aliases": {
            "month": ["month", "period"],
            "item": ["item", "item name"],
            "opening": ["opening"],
            "purchased": ["purchased", "purchase"],
            "used": ["used"],
            "closing": ["closing"],
            "required_next_month": ["required next month", "next month required"],
            "cost": ["cost", "amount"],
        },
    },
    "utilities": {
        "label": "Utility Bills",
        "sheet_aliases": ["utilities", "utility bills", "bills"],
        "required": ["utility"],
        "defaults": {"amount": 0, "status": "Pending", "reminder_sent": "No"},
        "date_columns": ["invoice_date", "due_date"],
        "numeric_columns": ["amount"],
        "aliases": {
            "utility": ["utility", "bill", "service"],
            "vendor": ["vendor", "supplier"],
            "invoice_date": ["invoice date", "bill date"],
            "due_date": ["due date"],
            "amount": ["amount", "cost"],
            "status": ["status"],
            "reminder_sent": ["reminder sent", "reminder"],
        },
    },
    "inventory": {
        "label": "Office Inventory",
        "sheet_aliases": ["inventory", "office inventory", "assets"],
        "required": ["item"],
        "defaults": {"quantity": 0},
        "numeric_columns": ["quantity"],
        "aliases": {
            "item": ["item", "asset", "item name"],
            "category": ["category"],
            "quantity": ["quantity", "qty"],
            "location": ["location"],
            "responsible_person": ["responsible person", "responsible", "owner"],
            "condition": ["condition"],
        },
    },
    "vendors": {
        "label": "Vendor Database",
        "sheet_aliases": ["vendors", "vendor database", "vendor"],
        "required": ["vendor"],
        "date_columns": ["renewal_date"],
        "aliases": {
            "vendor": ["vendor", "vendor name", "supplier"],
            "service": ["service"],
            "contact_person": ["contact person", "contact"],
            "mobile": ["mobile", "phone"],
            "contract_status": ["contract status", "status"],
            "renewal_date": ["renewal date"],
        },
    },
    "tasks": {
        "label": "P&C Task Calendar",
        "sheet_aliases": ["tasks", "p&c task calendar", "pc task calendar", "hr task calendar", "task calendar"],
        "required": ["task"],
        "defaults": {"status": "Pending"},
        "aliases": {
            "task": ["task", "activity"],
            "frequency": ["frequency"],
            "due_date": ["due date"],
            "status": ["status"],
            "remarks": ["remarks", "comments"],
        },
    },
}


def _db_columns(table_name: str) -> list[str]:
    return table_columns(table_name)


def _match_sheet(sheet_names: list[str], table_name: str) -> str | None:
    candidates = {_key(name): name for name in sheet_names}
    for alias in [table_name, *TABLES[table_name]["sheet_aliases"]]:
        if _key(alias) in candidates:
            return candidates[_key(alias)]
    return None


def _rename_map(df: pd.DataFrame, table_name: str) -> dict[str, str]:
    normalized_columns = {_key(col): col for col in df.columns}
    mapping = {}
    for db_col in _db_columns(table_name):
        aliases = [db_col, db_col.replace("_", " "), *TABLES[table_name].get("aliases", {}).get(db_col, [])]
        for alias in aliases:
            source_col = normalized_columns.get(_key(alias))
            if source_col is not None:
                mapping[source_col] = db_col
                break
    return mapping


def _clean_import_df(raw: pd.DataFrame, table_name: str) -> tuple[pd.DataFrame, list[str], list[str]]:
    raw = raw.dropna(how="all").copy()
    raw.columns = [str(col).strip() for col in raw.columns]
    raw = raw.rename(columns=_rename_map(raw, table_name))

    db_columns = _db_columns(table_name)
    recognized = [col for col in db_columns if col in raw.columns]
    clean = raw[recognized].copy()

    defaults = TABLES[table_name].get("defaults", {})
    for col in db_columns:
        if col not in clean.columns and col not in TABLES[table_name]["required"]:
            clean[col] = defaults.get(col, "")

    for col, value in defaults.items():
        if col in clean.columns:
            clean[col] = clean[col].fillna(value)

    missing = [col for col in TABLES[table_name]["required"] if col not in clean.columns or clean[col].replace("", pd.NA).isna().all()]
    clean = clean[[col for col in db_columns if col in clean.columns]]

    for col in TABLES[table_name].get("date_columns", []):
        if col in clean.columns:
            dates = pd.to_datetime(clean[col], errors="coerce")
            clean[col] = dates.dt.strftime("%Y-%m-%d").fillna("")

    for col in TABLES[table_name].get("numeric_columns", []):
        if col in clean.columns:
            clean[col] = pd.to_numeric(clean[col], errors="coerce").fillna(0)

    clean = clean.fillna("")
    ignored = [col for col in raw.columns if col not in db_columns]
    return clean, missing, ignored


def _backup_database() -> Path:
    backup_dir = DB_PATH.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"citi_homes_hris_before_import_{timestamp}.db"
    if not DB_PATH.exists():
        return backup_path
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def _template_workbook() -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for table_name, config in TABLES.items():
            columns = _db_columns(table_name)
            example = {col: "" for col in columns}
            for col, value in config.get("defaults", {}).items():
                if col in example:
                    example[col] = value
            pd.DataFrame([example]).to_excel(writer, index=False, sheet_name=config["label"][:31])
    return output.getvalue()


def show() -> None:
    user = st.session_state.get("user", {})
    if user.get("role") != "Admin":
        st.error("Excel Data Import is available for Admin users only.")
        return

    hero("Excel Data Import", "Upload your real P&C and operations workbook, preview the mapping, and replace selected tables after review.")

    st.warning("Import replaces only the selected tables. A database backup is saved automatically before anything changes.")

    c1, c2 = st.columns([2, 1])
    with c1:
        uploaded = st.file_uploader("Upload Excel workbook", type=["xlsx", "xls"])
    with c2:
        st.download_button(
            "Download import template",
            data=_template_workbook(),
            file_name="citi_homes_hris_import_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )

    if uploaded is None:
        section("Expected sheets")
        st.dataframe(
            pd.DataFrame(
                [{"P&C Section": cfg["label"], "Required Columns": ", ".join(cfg["required"])} for cfg in TABLES.values()]
            ),
            hide_index=True,
        )
        return

    try:
        workbook = pd.ExcelFile(uploaded)
    except Exception as exc:
        st.error(f"Could not read the workbook: {exc}")
        return

    section("Workbook review")
    st.caption(f"Sheets found: {', '.join(workbook.sheet_names)}")

    prepared: dict[str, pd.DataFrame] = {}
    errors: dict[str, list[str]] = {}
    selections: list[str] = []

    with st.form("excel_import_form"):
        for table_name, config in TABLES.items():
            default_sheet = _match_sheet(workbook.sheet_names, table_name)
            with st.expander(config["label"], expanded=default_sheet is not None):
                sheet_options = ["Do not import", *workbook.sheet_names]
                default_index = sheet_options.index(default_sheet) if default_sheet in sheet_options else 0
                selected_sheet = st.selectbox("Workbook sheet", sheet_options, index=default_index, key=f"sheet_{table_name}")
                if selected_sheet == "Do not import":
                    continue

                raw = pd.read_excel(workbook, sheet_name=selected_sheet)
                clean, missing, ignored = _clean_import_df(raw, table_name)
                if missing:
                    errors[table_name] = missing
                    st.error(f"Missing required columns: {', '.join(missing)}")
                else:
                    prepared[table_name] = clean
                    selections.append(table_name)
                    st.success(f"Ready to import {len(clean)} rows.")
                    st.dataframe(clean.head(10), hide_index=True)
                    if ignored:
                        st.caption(f"Ignored extra columns: {', '.join(ignored[:12])}")

        confirm = st.checkbox("I reviewed the preview and want to replace the selected P&C tables.")
        submitted = st.form_submit_button("Import selected sheets", width="stretch")

    if submitted:
        if not confirm:
            st.error("Please tick the review confirmation before importing.")
            return
        if errors:
            st.error("Please fix the missing required columns before importing.")
            return
        if not selections:
            st.error("No sheets were selected for import.")
            return

        try:
            backup_path = _backup_database()
            for table_name in selections:
                reset_table(table_name, prepared[table_name])
            st.success(f"Imported {len(selections)} table(s). Backup saved at {backup_path.name}.")
            st.rerun()
        except Exception as exc:
            st.error(f"Import failed. Your backup was created before changes. Error: {exc}")
