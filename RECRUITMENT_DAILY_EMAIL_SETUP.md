# Recruitment Daily Email Setup - Outlook

The report builder is ready at `scripts/send_recruitment_report.py`.

The Outlook setup sends the recruitment tracker CSV to `umer@citihomes.ae` Monday to Saturday at 17:00. Sunday is skipped.

Run this from the project folder:

```powershell
.\scripts\setup_outlook_recruitment_report.ps1
```

It uses the Outlook desktop app/profile signed in on this Windows user. No Outlook password is stored in the project.

To test immediately after setup:

```powershell
.\scripts\send_recruitment_report_outlook.ps1
```

Or double-click this file from File Explorer:

```text
scripts\test_outlook_recruitment_report.cmd
```

Keep Classic Outlook open during the test. If Outlook asks for permission to send, allow it. The newer web-style Outlook app may not support this Windows email automation.

The CSV can also be generated without email:

```powershell
.\.venv\Scripts\python.exe -c "from scripts.send_recruitment_report import build_report; print(build_report())"
```
