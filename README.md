# Citi Homes P&C & Administration Management System

A professional Streamlit-based People & Culture/Admin system for Citi Homes.

## Features

- Management dashboard
- Employee master database
- Manpower planning
- Recruitment tracker
- Interview evaluation
- Joining checklist
- Attendance portal link
- Leave management
- UAE visa/document expiry tracker
- Pantry management
- Utility bill tracker
- Office inventory
- Vendor database
- Monthly P&C report generator
- P&C task calendar
- Excel exports
- Login screen with Admin and Management roles

## Default Login

Admin:
- Username: `admin`
- Password: `admin123`

Management:
- Username: `management`
- Password: `management123`

Change default passwords before live use.

## How to Run

Open PowerShell in the project folder and run:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

If Streamlit is not recognized, use:

```bash
python -m streamlit run app.py
```

## Database

The system uses SQLite and automatically creates `citi_homes_hris.db` on first run.

## Attendance Portal SSO

The Attendance Portal page can generate a short-lived signed launch URL for Admin users. This is the safe replacement for storing the Attendance Portal admin password in the HRMS.

See `ATTENDANCE_SSO_SETUP.md` for the HRMS secret setup and the required Supabase/Attendance Portal verifier.

## Import Excel Data

Log in as Admin and open **Excel Data Import** from the sidebar.

1. Download the import template, or prepare an Excel workbook with sheets such as Employee Master, Recruitment Tracker, Attendance Portal, Visa & Documents, Pantry Management, Utility Bills, Office Inventory, Vendor Database, and P&C Task Calendar.
2. Upload the workbook.
3. Review the preview for each matched sheet.
4. Confirm the import to replace the selected P&C tables.

The app creates a backup of the current SQLite database in the `backups` folder before importing.
