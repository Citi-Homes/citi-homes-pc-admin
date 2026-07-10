from __future__ import annotations

from datetime import date, datetime
from typing import Any
from urllib.parse import urlencode

import pandas as pd
import requests

from config import ATTENDANCE_SUPABASE_ANON_KEY, ATTENDANCE_SUPABASE_URL

ATTENDANCE_TABLE = "attendance_records"


def _headers() -> dict[str, str]:
    return {
        "apikey": ATTENDANCE_SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {ATTENDANCE_SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
    }


def _parse_time(value: str) -> datetime | None:
    if not value:
        return None
    text = str(value)
    time_part = text.split("·")[-1].strip() if "·" in text else text.strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(time_part, fmt)
        except ValueError:
            continue
    return None


def _hours_between(punch_in: str, punch_out: str) -> float:
    start = _parse_time(punch_in)
    end = _parse_time(punch_out)
    if start is None or end is None:
        return 0.0
    minutes = (end - start).total_seconds() / 60
    if minutes < 0:
        minutes += 24 * 60
    return round(minutes / 60, 2)


def _format_hours(hours: float) -> str:
    total_minutes = int(round(float(hours) * 60))
    return f"{total_minutes // 60}h {total_minutes % 60:02d}m"


def _record_date(row: dict[str, Any]) -> str:
    if row.get("record_date"):
        return str(row["record_date"])[:10]
    punch_in = str(row.get("punch_in") or "")
    match = pd.to_datetime(punch_in.split("·")[0].strip(), errors="coerce")
    if pd.notna(match):
        return match.strftime("%Y-%m-%d")
    return ""


def fetch_attendance_records(limit: int = 1000) -> pd.DataFrame:
    params = urlencode({"select": "*", "order": "id.desc", "limit": limit})
    url = f"{ATTENDANCE_SUPABASE_URL.rstrip('/')}/rest/v1/{ATTENDANCE_TABLE}?{params}"
    response = requests.get(url, headers=_headers(), timeout=20)
    response.raise_for_status()
    rows = response.json()
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["record_date"] = [_record_date(row) for row in rows]
    df["hours"] = [
        _hours_between(row.get("punch_in") or "", row.get("punch_out") or "")
        for row in rows
    ]
    df["hours_label"] = df["hours"].map(_format_hours)
    return df


def attendance_summary(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "employees": 0,
            "checkins_today": 0,
            "records": 0,
            "total_hours": 0.0,
            "missing_punchouts": 0,
        }

    today = date.today().isoformat()
    punch_out = df.get("punch_out", pd.Series(dtype=str)).fillna("").astype(str)
    return {
        "employees": int(df.get("emp_code", pd.Series(dtype=str)).nunique()),
        "checkins_today": int((df["record_date"] == today).sum()),
        "records": int(len(df)),
        "total_hours": round(float(pd.to_numeric(df["hours"], errors="coerce").fillna(0).sum()), 2),
        "missing_punchouts": int((punch_out == "").sum()),
    }


def hours_by_employee(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    grouped = (
        df.groupby(["emp_code", "emp_name", "department"], dropna=False)
        .agg(
            days=("record_date", "nunique"),
            total_hours=("hours", "sum"),
            office=("category", lambda s: int((s == "Office").sum())),
            procurement=("category", lambda s: int((s == "Procurement").sum())),
            interview=("category", lambda s: int((s == "Interview").sum())),
        )
        .reset_index()
        .sort_values("total_hours", ascending=False)
    )
    grouped["total_hours"] = grouped["total_hours"].round(2)
    grouped["regular_hours"] = grouped["days"].astype(float).mul(8).clip(upper=grouped["total_hours"]).round(2)
    grouped["overtime_hours"] = (grouped["total_hours"] - grouped["regular_hours"]).clip(lower=0).round(2)
    grouped["avg_hours_day"] = (grouped["total_hours"] / grouped["days"].replace(0, pd.NA)).fillna(0).round(2)
    return grouped


def display_records(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cols = [
        "record_date",
        "emp_code",
        "emp_name",
        "department",
        "category",
        "punch_in",
        "punch_out",
        "hours_label",
        "remarks",
        "status",
    ]
    available = [col for col in cols if col in df.columns]
    out = df[available].copy()
    out.columns = [
        "Date",
        "Emp Code",
        "Name",
        "Dept",
        "Category",
        "Punch In",
        "Punch Out",
        "Hours",
        "Remarks",
        "Status",
    ][: len(out.columns)]
    return out
