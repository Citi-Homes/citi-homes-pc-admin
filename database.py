import hashlib
import math
import re
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlencode

import pandas as pd
import requests
import streamlit as st

from config import DB_PATH


TABLE_COLUMNS: dict[str, list[str]] = {
    "users": ["id", "username", "password_hash", "full_name", "role", "is_active"],
    "employees": ["id", "employee_id", "name", "department", "designation", "nationality", "joining_date", "employment_type", "visa_status", "emirates_id_expiry", "passport_expiry", "mobile", "emergency_contact", "status"],
    "manpower": ["id", "department", "position", "required", "available", "priority", "status"],
    "recruitment": ["id", "candidate", "position", "source", "mobile", "location", "gcc_experience", "total_experience", "current_salary", "expected_salary", "notice_period", "interview_date", "status"],
    "interview_evaluation": ["id", "recruitment_id", "candidate", "position", "department", "interviewer_names", "interview_date", "technical_score", "experience_score", "communication_score", "technical_knowledge", "position_specific_skills", "relevant_experience", "problem_solving_ability", "teamwork", "operations_overall_impression", "operations_strengths", "operations_improvements", "operations_remarks", "operations_recommendation", "operations_comments", "communication_skills", "confidence_professionalism", "personality_attitude", "personality_assessment", "pc_strengths", "pc_improvements", "pc_remarks", "pc_recommendation", "pc_comments", "recommended_salary", "final_notice_period", "final_remarks", "operations_signature", "pc_signature", "final_decision", "interviewer_comments"],
    "joining_checklist": ["id", "employee", "offer_letter", "passport_copy", "visa", "emirates_id", "medical", "contract", "insurance", "bank_details", "completed_pct"],
    "attendance": ["id", "employee", "department", "month", "working_days", "present", "absent", "late", "overtime", "remarks"],
    "leave_management": ["id", "employee", "leave_type", "opening_balance", "used", "remaining"],
    "documents": ["id", "employee", "document", "expiry_date", "reminder_date", "status"],
    "pantry": ["id", "month", "item", "opening", "purchased", "used", "closing", "required_next_month", "cost"],
    "utilities": ["id", "utility", "vendor", "invoice_date", "due_date", "amount", "status", "reminder_sent"],
    "inventory": ["id", "item", "category", "quantity", "location", "responsible_person", "condition"],
    "vendors": ["id", "vendor", "service", "contact_person", "mobile", "contract_status", "renewal_date"],
    "tasks": ["id", "task", "frequency", "due_date", "status", "remarks"],
}


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _supabase_config() -> tuple[str, str] | None:
    try:
        config = st.secrets.get("supabase", {})
    except Exception:
        return None
    url = str(config.get("url") or "").strip().rstrip("/")
    key = str(config.get("service_role_key") or config.get("anon_key") or "").strip()
    if not url or not key:
        return None
    return url, key


def using_supabase() -> bool:
    try:
        config = st.secrets.get("data", {})
        backend = str(config.get("backend") or "").strip().lower()
        if backend == "sqlite":
            return False
    except Exception:
        pass
    return _supabase_config() is not None


def table_columns(table_name: str, include_id: bool = False) -> list[str]:
    columns = TABLE_COLUMNS.get(table_name, [])
    if include_id:
        return columns.copy()
    return [column for column in columns if column != "id"]


def _supabase_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    config = _supabase_config()
    if config is None:
        raise RuntimeError("Supabase is not configured.")
    _, key = config
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    if extra:
        headers.update(extra)
    return headers


def _supabase_url(table_name: str, query: str = "") -> str:
    config = _supabase_config()
    if config is None:
        raise RuntimeError("Supabase is not configured.")
    url, _ = config
    suffix = f"?{query}" if query else ""
    return f"{url}/rest/v1/{table_name}{suffix}"


def _clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _clean_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    clean = df.astype(object).where(pd.notna(df), None)
    rows = clean.to_dict(orient="records")
    return [{key: _clean_value(value) for key, value in row.items()} for row in rows]


def _split_columns(columns: str) -> list[str]:
    return [col.strip().strip('"') for col in columns.replace("\n", " ").split(",") if col.strip()]


def _extract_table(query: str) -> str:
    match = re.search(r"\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)", query, re.IGNORECASE)
    if not match:
        match = re.search(r"\b(?:INTO|UPDATE|DELETE\s+FROM)\s+([a-zA-Z_][a-zA-Z0-9_]*)", query, re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not identify table in query: {query}")
    return match.group(1)


def _fetch_supabase_table(table_name: str) -> pd.DataFrame:
    params = urlencode({"select": "*", "order": "id.asc", "limit": 10000})
    response = requests.get(_supabase_url(table_name, params), headers=_supabase_headers(), timeout=30)
    response.raise_for_status()
    df = pd.DataFrame(response.json())
    columns = TABLE_COLUMNS.get(table_name)
    if columns:
        for column in columns:
            if column not in df.columns:
                df[column] = None
        df = df[columns]
    return df


def _apply_where(df: pd.DataFrame, query: str, params: Iterable[Any] | None = None) -> pd.DataFrame:
    if df.empty or "WHERE" not in query.upper():
        return df
    out = df.copy()
    params_list = list(params or [])

    if "recruitment_id=?" in query.replace(" ", "") and params_list:
        out = out[pd.to_numeric(out["recruitment_id"], errors="coerce") == int(params_list[0])]
    if "recruitment_id IS NOT NULL" in query.upper() and "recruitment_id" in out.columns:
        out = out[out["recruitment_id"].notna()]
    if "interview_date IS NOT NULL" in query.upper() and "interview_date" in out.columns:
        dates = out["interview_date"].fillna("").astype(str).str.strip()
        out = out[dates != ""]
    return out


def _apply_select(df: pd.DataFrame, query: str) -> pd.DataFrame:
    select_match = re.search(r"SELECT\s+(.*?)\s+FROM\s+", query, re.IGNORECASE | re.DOTALL)
    if not select_match:
        return df
    select_part = " ".join(select_match.group(1).split())
    if select_part == "*":
        return df
    if select_part.startswith("*,") and "required - available" in select_part:
        if {"required", "available"}.issubset(df.columns):
            df = df.copy()
            df["gap"] = pd.to_numeric(df["required"], errors="coerce").fillna(0) - pd.to_numeric(df["available"], errors="coerce").fillna(0)
        return df
    columns = [col for col in _split_columns(select_part) if col in df.columns]
    return df[columns].copy() if columns else df


def _apply_order(df: pd.DataFrame, query: str) -> pd.DataFrame:
    match = re.search(r"ORDER\s+BY\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(ASC|DESC)?", query, re.IGNORECASE)
    if not match or match.group(1) not in df.columns:
        return df
    ascending = (match.group(2) or "ASC").upper() != "DESC"
    return df.sort_values(match.group(1), ascending=ascending, kind="stable").reset_index(drop=True)


def _supabase_fetch_df(query: str, params: Iterable[Any] | None = None) -> pd.DataFrame:
    table_name = _extract_table(query)
    df = _fetch_supabase_table(table_name)
    df = _apply_where(df, query, params)
    df = _apply_order(df, query)
    df = _apply_select(df, query)
    return df.reset_index(drop=True)


def _supabase_execute(query: str, params: Iterable[Any] | None = None) -> None:
    compact = " ".join(query.strip().split())
    params_list = [_clean_value(value) for value in list(params or [])]

    insert_match = re.search(r"INSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)\s*VALUES", compact, re.IGNORECASE)
    if insert_match:
        table_name = insert_match.group(1)
        columns = _split_columns(insert_match.group(2))
        payload = {column: params_list[index] for index, column in enumerate(columns)}
        response = requests.post(_supabase_url(table_name), headers=_supabase_headers(), json=payload, timeout=30)
        response.raise_for_status()
        return

    update_match = re.search(r"UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+SET\s+(.*?)\s+WHERE\s+([a-zA-Z_][a-zA-Z0-9_]*)=\?", compact, re.IGNORECASE)
    if update_match:
        table_name = update_match.group(1)
        assignments = [part.strip() for part in update_match.group(2).split(",")]
        columns = [part.split("=", 1)[0].strip() for part in assignments]
        where_column = update_match.group(3)
        payload = {column: params_list[index] for index, column in enumerate(columns)}
        where_value = params_list[len(columns)]
        filter_query = urlencode({where_column: f"eq.{where_value}"})
        response = requests.patch(_supabase_url(table_name, filter_query), headers=_supabase_headers(), json=payload, timeout=30)
        response.raise_for_status()
        return

    delete_match = re.search(r"DELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)", compact, re.IGNORECASE)
    if delete_match:
        table_name = delete_match.group(1)
        response = requests.delete(_supabase_url(table_name, "id=not.is.null"), headers=_supabase_headers(), timeout=30)
        response.raise_for_status()
        return

    raise NotImplementedError(f"Supabase database layer does not support this query yet: {query}")


def execute(query: str, params: Iterable[Any] | None = None) -> None:
    if using_supabase():
        _supabase_execute(query, params)
        return
    conn = get_connection()
    try:
        conn.execute(query, tuple(params or []))
        conn.commit()
    finally:
        conn.close()


def fetch_df(query: str, params: Iterable[Any] | None = None) -> pd.DataFrame:
    if using_supabase():
        return _supabase_fetch_df(query, params)
    conn = get_connection()
    try:
        return pd.read_sql_query(query, conn, params=tuple(params or []))
    finally:
        conn.close()


def authenticate(username: str, password: str) -> dict[str, Any] | None:
    if using_supabase():
        users = fetch_df("SELECT username, full_name, role, password_hash, is_active FROM users")
        if users.empty:
            return None
        username_clean = username.strip().lower()
        matches = users[
            (users["username"].astype(str).str.lower() == username_clean)
            & (users["password_hash"] == hash_password(password))
            & (pd.to_numeric(users["is_active"], errors="coerce").fillna(0).astype(int) == 1)
        ]
        if matches.empty:
            return None
        row = matches.iloc[0]
        return {"username": row["username"], "full_name": row["full_name"], "role": row["role"]}

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT username, full_name, role FROM users WHERE username=? AND password_hash=? AND is_active=1",
            (username.strip().lower(), hash_password(password)),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_tables() -> None:
    if using_supabase():
        return
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Admin',
            is_active INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            nationality TEXT,
            joining_date TEXT,
            employment_type TEXT,
            visa_status TEXT,
            emirates_id_expiry TEXT,
            passport_expiry TEXT,
            mobile TEXT,
            emergency_contact TEXT,
            status TEXT DEFAULT 'Active'
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS manpower (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT NOT NULL,
            position TEXT NOT NULL,
            required INTEGER NOT NULL DEFAULT 0,
            available INTEGER NOT NULL DEFAULT 0,
            priority TEXT NOT NULL DEFAULT 'Medium',
            status TEXT NOT NULL DEFAULT 'Open'
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS recruitment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate TEXT NOT NULL,
            position TEXT NOT NULL,
            source TEXT,
            mobile TEXT,
            location TEXT,
            gcc_experience REAL DEFAULT 0,
            total_experience REAL DEFAULT 0,
            current_salary REAL DEFAULT 0,
            expected_salary REAL DEFAULT 0,
            notice_period TEXT,
            interview_date TEXT,
            status TEXT NOT NULL DEFAULT 'Applied'
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS interview_evaluation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recruitment_id INTEGER,
            candidate TEXT NOT NULL,
            position TEXT NOT NULL,
            department TEXT,
            interviewer_names TEXT,
            interview_date TEXT,
            technical_score INTEGER DEFAULT 1,
            experience_score INTEGER DEFAULT 1,
            communication_score INTEGER DEFAULT 1,
            technical_knowledge INTEGER DEFAULT 1,
            position_specific_skills INTEGER DEFAULT 1,
            relevant_experience INTEGER DEFAULT 1,
            problem_solving_ability INTEGER DEFAULT 1,
            teamwork INTEGER DEFAULT 1,
            operations_overall_impression INTEGER DEFAULT 1,
            operations_strengths TEXT,
            operations_improvements TEXT,
            operations_remarks TEXT,
            operations_recommendation TEXT,
            operations_comments TEXT,
            communication_skills INTEGER DEFAULT 1,
            confidence_professionalism INTEGER DEFAULT 1,
            personality_attitude INTEGER DEFAULT 1,
            personality_assessment INTEGER DEFAULT 1,
            pc_strengths TEXT,
            pc_improvements TEXT,
            pc_remarks TEXT,
            pc_recommendation TEXT,
            pc_comments TEXT,
            recommended_salary REAL DEFAULT 0,
            final_notice_period TEXT,
            final_remarks TEXT,
            operations_signature TEXT,
            pc_signature TEXT,
            final_decision TEXT,
            interviewer_comments TEXT
        )
        """
    )

    _ensure_columns(
        cur,
        "interview_evaluation",
        {
            "recruitment_id": "INTEGER",
            "department": "TEXT",
            "interviewer_names": "TEXT",
            "technical_knowledge": "INTEGER DEFAULT 1",
            "position_specific_skills": "INTEGER DEFAULT 1",
            "relevant_experience": "INTEGER DEFAULT 1",
            "problem_solving_ability": "INTEGER DEFAULT 1",
            "teamwork": "INTEGER DEFAULT 1",
            "operations_overall_impression": "INTEGER DEFAULT 1",
            "operations_strengths": "TEXT",
            "operations_improvements": "TEXT",
            "operations_remarks": "TEXT",
            "operations_recommendation": "TEXT",
            "operations_comments": "TEXT",
            "communication_skills": "INTEGER DEFAULT 1",
            "confidence_professionalism": "INTEGER DEFAULT 1",
            "personality_attitude": "INTEGER DEFAULT 1",
            "personality_assessment": "INTEGER DEFAULT 1",
            "pc_strengths": "TEXT",
            "pc_improvements": "TEXT",
            "pc_remarks": "TEXT",
            "pc_recommendation": "TEXT",
            "pc_comments": "TEXT",
            "recommended_salary": "REAL DEFAULT 0",
            "final_notice_period": "TEXT",
            "final_remarks": "TEXT",
            "operations_signature": "TEXT",
            "pc_signature": "TEXT",
        },
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS joining_checklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee TEXT NOT NULL,
            offer_letter TEXT DEFAULT 'Pending',
            passport_copy TEXT DEFAULT 'Pending',
            visa TEXT DEFAULT 'Pending',
            emirates_id TEXT DEFAULT 'Pending',
            medical TEXT DEFAULT 'Pending',
            contract TEXT DEFAULT 'Pending',
            insurance TEXT DEFAULT 'Pending',
            bank_details TEXT DEFAULT 'Pending',
            completed_pct REAL DEFAULT 0
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee TEXT NOT NULL,
            department TEXT,
            month TEXT,
            working_days INTEGER DEFAULT 0,
            present INTEGER DEFAULT 0,
            absent INTEGER DEFAULT 0,
            late INTEGER DEFAULT 0,
            overtime REAL DEFAULT 0,
            remarks TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS leave_management (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            opening_balance REAL DEFAULT 0,
            used REAL DEFAULT 0,
            remaining REAL DEFAULT 0
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee TEXT NOT NULL,
            document TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            reminder_date TEXT,
            status TEXT DEFAULT 'Valid'
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pantry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT,
            item TEXT NOT NULL,
            opening REAL DEFAULT 0,
            purchased REAL DEFAULT 0,
            used REAL DEFAULT 0,
            closing REAL DEFAULT 0,
            required_next_month REAL DEFAULT 0,
            cost REAL DEFAULT 0
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS utilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utility TEXT NOT NULL,
            vendor TEXT,
            invoice_date TEXT,
            due_date TEXT,
            amount REAL DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            reminder_sent TEXT DEFAULT 'No'
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            category TEXT,
            quantity INTEGER DEFAULT 0,
            location TEXT,
            responsible_person TEXT,
            condition TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor TEXT NOT NULL,
            service TEXT,
            contact_person TEXT,
            mobile TEXT,
            contract_status TEXT,
            renewal_date TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            frequency TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'Pending',
            remarks TEXT
        )
        """
    )

    conn.commit()
    seed_data(conn)
    conn.close()


def _ensure_columns(cur: sqlite3.Cursor, table_name: str, columns: dict[str, str]) -> None:
    existing = {row["name"] for row in cur.execute(f"PRAGMA table_info({table_name})").fetchall()}
    for column, definition in columns.items():
        if column not in existing:
            cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column} {definition}")


def table_is_empty(conn: sqlite3.Connection, table_name: str) -> bool:
    count = conn.execute(f"SELECT COUNT(*) AS c FROM {table_name}").fetchone()["c"]
    return count == 0


def seed_data(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    if table_is_empty(conn, "users"):
        cur.executemany(
            "INSERT INTO users(username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            [
                ("admin", hash_password("admin123"), "P&C Administrator", "Admin"),
                ("management", hash_password("management123"), "Management View", "Management"),
            ],
        )

    if table_is_empty(conn, "employees"):
        employees = [
            ("CH001", "Ahmed Ali", "Production", "Carpenter", "Pakistan", "2026-07-01", "Employee", "Processing", "2028-09-20", "2030-05-15", "0500000001", "Brother", "Active"),
            ("CH002", "Muhammad Irfan", "Operations", "Operations Manager", "Pakistan", "2026-06-10", "Employee", "Issued", "2028-06-20", "2031-02-10", "0500000002", "Wife", "Active"),
            ("CH003", "Nadeem Anwar", "Production", "Upholsterer", "Pakistan", "2026-07-05", "Employee", "Processing", "2026-07-25", "2029-11-01", "0500000003", "Brother", "Active"),
            ("CH004", "John Mathew", "Warehouse", "Forklift Driver", "India", "2026-07-08", "Employee", "Not Started", "2027-02-12", "2029-08-22", "0500000004", "Friend", "Active"),
        ]
        cur.executemany(
            """
            INSERT INTO employees(employee_id, name, department, designation, nationality, joining_date, employment_type, visa_status, emirates_id_expiry, passport_expiry, mobile, emergency_contact, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            employees,
        )

    if table_is_empty(conn, "manpower"):
        rows = [
            ("Production", "Carpenter", 20, 5, "High", "Open"),
            ("Production", "Upholsterer", 15, 3, "High", "Open"),
            ("Warehouse", "Forklift Driver", 2, 0, "Medium", "Open"),
            ("Painting", "Painter", 6, 1, "High", "Open"),
            ("Production", "Helper", 10, 2, "Medium", "Open"),
        ]
        cur.executemany(
            "INSERT INTO manpower(department, position, required, available, priority, status) VALUES (?, ?, ?, ?, ?, ?)", rows
        )

    if table_is_empty(conn, "recruitment"):
        rows = [
            ("Sajjad Khan", "Production Manager", "LinkedIn", "0501111111", "UAE", 12, 15, 14000, 17000, "30 Days", "2026-07-15", "Interview Scheduled"),
            ("Ramesh Kumar", "Carpenter", "WhatsApp Group", "0502222222", "UAE", 5, 9, 2500, 3200, "Immediate", "2026-07-14", "Shortlisted"),
            ("Bilal Ahmed", "Upholsterer", "Referral", "0503333333", "UAE", 4, 8, 2300, 3000, "15 Days", "2026-07-16", "Selected"),
            ("Joseph Paul", "Forklift Driver", "Indeed", "0504444444", "UAE", 7, 10, 2800, 3500, "Immediate", "2026-07-17", "Offer Sent"),
            ("Adeel Khan", "Painter", "LinkedIn", "0505555555", "Pakistan", 0, 6, 0, 2500, "Visit Visa", "", "Applied"),
        ]
        cur.executemany(
            """
            INSERT INTO recruitment(candidate, position, source, mobile, location, gcc_experience, total_experience, current_salary, expected_salary, notice_period, interview_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    if table_is_empty(conn, "interview_evaluation"):
        cur.executemany(
            """
            INSERT INTO interview_evaluation(candidate, position, interview_date, technical_score, experience_score, communication_score, final_decision, interviewer_comments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("Bilal Ahmed", "Upholsterer", "2026-07-16", 4, 4, 3, "Selected", "Good upholstery experience and can join within 15 days."),
                ("Ramesh Kumar", "Carpenter", "2026-07-14", 4, 5, 3, "Second Interview", "Strong furniture manufacturing background."),
            ],
        )

    if table_is_empty(conn, "joining_checklist"):
        cur.executemany(
            """
            INSERT INTO joining_checklist(employee, offer_letter, passport_copy, visa, emirates_id, medical, contract, insurance, bank_details, completed_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("Ahmed Ali", "Received", "Received", "Pending", "Pending", "Pending", "Received", "Pending", "Received", 50),
                ("Nadeem Anwar", "Received", "Received", "Pending", "Pending", "Pending", "Pending", "Pending", "Pending", 25),
            ],
        )

    if table_is_empty(conn, "attendance"):
        cur.executemany(
            """
            INSERT INTO attendance(employee, department, month, working_days, present, absent, late, overtime, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("Ahmed Ali", "Production", "July 2026", 26, 20, 1, 2, 12, "Good attendance"),
                ("Muhammad Irfan", "Operations", "July 2026", 26, 21, 0, 0, 6, ""),
                ("Nadeem Anwar", "Production", "July 2026", 26, 19, 2, 1, 8, "Monitor lateness"),
            ],
        )

    if table_is_empty(conn, "leave_management"):
        cur.executemany(
            "INSERT INTO leave_management(employee, leave_type, opening_balance, used, remaining) VALUES (?, ?, ?, ?, ?)",
            [
                ("Ahmed Ali", "Annual Leave", 30, 0, 30),
                ("Muhammad Irfan", "Annual Leave", 30, 2, 28),
                ("Nadeem Anwar", "Sick Leave", 15, 1, 14),
            ],
        )

    if table_is_empty(conn, "documents"):
        today = date.today()
        docs = [
            ("Ahmed Ali", "Emirates ID", str(today + timedelta(days=20)), str(today - timedelta(days=10)), "Expiring Soon"),
            ("Ahmed Ali", "Passport", "2030-05-15", "2030-04-15", "Valid"),
            ("Nadeem Anwar", "Visa", str(today - timedelta(days=3)), str(today - timedelta(days=33)), "Expired"),
            ("John Mathew", "Labour Contract", str(today + timedelta(days=120)), str(today + timedelta(days=90)), "Valid"),
        ]
        cur.executemany(
            "INSERT INTO documents(employee, document, expiry_date, reminder_date, status) VALUES (?, ?, ?, ?, ?)", docs
        )

    if table_is_empty(conn, "pantry"):
        cur.executemany(
            "INSERT INTO pantry(month, item, opening, purchased, used, closing, required_next_month, cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("July 2026", "Tea", 5, 10, 8, 7, 10, 150),
                ("July 2026", "Coffee", 2, 5, 3, 4, 5, 220),
                ("July 2026", "Milk Tins", 12, 24, 20, 16, 30, 360),
                ("July 2026", "Sugar", 3, 6, 4, 5, 8, 95),
            ],
        )

    if table_is_empty(conn, "utilities"):
        cur.executemany(
            "INSERT INTO utilities(utility, vendor, invoice_date, due_date, amount, status, reminder_sent) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("Electricity", "FEWA", "2026-07-01", "2026-07-10", 4500, "Pending", "No"),
                ("Internet", "Etisalat", "2026-07-02", "2026-07-12", 650, "Submitted", "Yes"),
                ("Water", "FEWA", "2026-07-03", "2026-07-15", 1200, "Paid", "Yes"),
            ],
        )

    if table_is_empty(conn, "inventory"):
        cur.executemany(
            "INSERT INTO inventory(item, category, quantity, location, responsible_person, condition) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("Laptop", "IT", 3, "Umm Al Quwain Office", "P&C Admin", "Good"),
                ("Printer", "Office Equipment", 1, "P&C Office", "P&C Admin", "Good"),
                ("Safety Shoes", "PPE", 20, "Warehouse", "Store Keeper", "New"),
            ],
        )

    if table_is_empty(conn, "vendors"):
        cur.executemany(
            "INSERT INTO vendors(vendor, service, contact_person, mobile, contract_status, renewal_date) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("ABC Cleaning", "Cleaning", "Mr. Saleem", "0507777777", "Active", "2027-01-01"),
                ("Secure Guard LLC", "Security", "Mr. Arun", "0508888888", "Under Review", "2026-08-30"),
            ],
        )

    if table_is_empty(conn, "tasks"):
        cur.executemany(
            "INSERT INTO tasks(task, frequency, due_date, status, remarks) VALUES (?, ?, ?, ?, ?)",
            [
                ("Attendance Report", "Monthly", "3rd of every month", "Pending", "Prepare and send to management"),
                ("Pantry Requirement", "Monthly", "25th of every month", "Completed", "Collect requirement from office/factory"),
                ("Utility Reminder", "Monthly", "10th of every month", "Pending", "Share pending bills with management"),
                ("Recruitment Pipeline Update", "Weekly", "Every Friday", "In Progress", "Update open positions and interview status"),
            ],
        )

    conn.commit()


def update_document_statuses() -> None:
    df = fetch_df("SELECT id, expiry_date FROM documents")
    today = pd.Timestamp.today().normalize()
    if using_supabase():
        for _, row in df.iterrows():
            expiry = pd.to_datetime(row["expiry_date"], errors="coerce")
            if pd.isna(expiry):
                status = "Valid"
            elif expiry < today:
                status = "Expired"
            elif expiry <= today + pd.Timedelta(days=30):
                status = "Expiring Soon"
            else:
                status = "Valid"
            execute("UPDATE documents SET status=? WHERE id=?", (status, int(row["id"])))
        return

    conn = get_connection()
    try:
        for _, row in df.iterrows():
            expiry = pd.to_datetime(row["expiry_date"], errors="coerce")
            if pd.isna(expiry):
                status = "Valid"
            elif expiry < today:
                status = "Expired"
            elif expiry <= today + pd.Timedelta(days=30):
                status = "Expiring Soon"
            else:
                status = "Valid"
            conn.execute("UPDATE documents SET status=? WHERE id=?", (status, int(row["id"])))
        conn.commit()
    finally:
        conn.close()


def reset_table(table_name: str, df: pd.DataFrame) -> None:
    if using_supabase():
        clean = df.copy()
        clean = clean.drop(columns=["id", "Sr. No"], errors="ignore")
        allowed = table_columns(table_name)
        clean = clean[[col for col in clean.columns if col in allowed]]
        _supabase_execute(f"DELETE FROM {table_name}")
        append_rows(table_name, clean)
        return

    conn = get_connection()
    try:
        clean = df.copy()
        if "id" in clean.columns:
            clean = clean.drop(columns=["id"])
        if "Sr. No" in clean.columns:
            clean = clean.drop(columns=["Sr. No"])
        conn.execute(f"DELETE FROM {table_name}")
        clean.to_sql(table_name, conn, if_exists="append", index=False)
        conn.commit()
    finally:
        conn.close()


def append_rows(table_name: str, df: pd.DataFrame) -> None:
    clean = df.copy()
    clean = clean.drop(columns=["id", "Sr. No"], errors="ignore")
    allowed = table_columns(table_name)
    clean = clean[[col for col in clean.columns if col in allowed]]
    if using_supabase():
        rows = _clean_rows(clean)
        if not rows:
            return
        response = requests.post(
            _supabase_url(table_name),
            headers=_supabase_headers({"Prefer": "return=minimal"}),
            json=rows,
            timeout=60,
        )
        response.raise_for_status()
        return

    conn = get_connection()
    try:
        clean.to_sql(table_name, conn, if_exists="append", index=False)
        conn.commit()
    finally:
        conn.close()
