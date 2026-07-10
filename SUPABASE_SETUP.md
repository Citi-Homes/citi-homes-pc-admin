# Citi Homes HRIS Supabase Setup

This keeps the app free-friendly and avoids Azure hosting. Supabase will store the app data online, while Streamlit continues to run the interface.

## 1. Create Supabase Project

1. Open https://supabase.com and create a free project.
2. Go to **Project Settings > API**.
3. Copy:
   - Project URL
   - `service_role` key

Keep the service role key private.

## 2. Create Tables

1. Open **SQL Editor** in Supabase.
2. Paste and run the full file:
   `scripts/supabase_schema.sql`

## 3. Add Local Secrets

Create or update:
`.streamlit/secrets.toml`

Add:

```toml
[supabase]
url = "https://YOUR_PROJECT.supabase.co"
service_role_key = "YOUR_SERVICE_ROLE_KEY"
```

## 4. Copy Current Local Data Online

From the project folder, run:

```powershell
.\.venv\Scripts\python.exe .\scripts\migrate_sqlite_to_supabase.py
```

After it finishes, run this in the Supabase SQL Editor:

`scripts/supabase_reset_sequences.sql`

## 5. Check Inside The App

Login as Admin and open:

**Supabase Setup**

Use **Test Supabase Connection** and **Refresh Supabase Counts**.

## Important

The current app is still using the local database until we confirm the online tables and switch the live data layer. This is intentional so no recent records are lost.
