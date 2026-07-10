# Streamlit Cloud Hosting

Use this for the free hosted app. The app code goes to GitHub, and the private Supabase key goes only into Streamlit Cloud secrets.

## What To Upload To GitHub

Upload the project folder contents, but do not upload these local/private items:

- `.venv/`
- `.streamlit/secrets.toml`
- `citi_homes_hris.db`
- `backups/`
- `logs/`
- generated report files in `reports/`

The `.gitignore` file already blocks those.

## Streamlit Cloud Settings

1. Open https://share.streamlit.io/
2. Sign in with GitHub.
3. Create a new app from the GitHub repository.
4. Set the main file path to:

```text
app.py
```

5. In app secrets, add:

```toml
[supabase]
url = "https://xcddssirxwhywvhspica.supabase.co"
service_role_key = "PASTE_THE_SUPABASE_SECRET_KEY_HERE"

[data]
backend = "supabase"
```

Do not put the real `service_role_key` into GitHub.

## Important Notes

- The hosted app will use Supabase as the live database.
- The local SQLite database is only a backup now.
- Outlook Desktop scheduled email will not run from Streamlit Cloud because Streamlit Cloud cannot control your local Outlook app. We can replace that later with a cloud email sender.
- The attendance portal link will continue to open the existing attendance portal.
