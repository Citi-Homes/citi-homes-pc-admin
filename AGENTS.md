# AGENTS.md

## Cursor Cloud specific instructions

### Primary product

The **Administration Portal** is a static SPA (`index.html` + `assets/`) deployed to **GitHub Pages**. It authenticates via **Supabase Auth** and reads/writes HR tables through Supabase REST with RLS policies.

- **Live URL:** https://citi-homes.github.io/citi-homes-pc-admin/
- **Supabase project:** `xcddssirxwhywvhspica` (config in `assets/supabase-config.js`)
- **Deploy:** push to `main` → `.github/workflows/pages.yml` publishes the repo root as static files

**Do not** run Streamlit, create local SQLite databases, or start local dev servers. The app runs on **GitHub Pages** only. Do not modify `app.py`, `.streamlit/`, `requirements.txt`, or other Streamlit/local paths unless the user explicitly asks.

### Services

| Service | Required? | Notes |
|---------|-----------|-------|
| GitHub Pages (deployed portal) | **MUST** | Primary way to run/test the app |
| Supabase HRIS (`xcddssirxwhywvhspica`) | **MUST** | Auth + all table CRUD |
| jsdelivr CDN | **MUST** (network) | Loads `@supabase/supabase-js` and `xlsx` |
| External Attendance Portal | OPTIONAL | Linked from nav only |
| Streamlit / SQLite | OUT OF SCOPE | Not used for this portal |

### Development workflow

There is **no build step** and **no package manager** for the static portal. Dependencies load from CDN at runtime.

1. Edit `index.html`, `assets/admin-clean.js`, `assets/admin.css`, or `assets/supabase-config.js`.
2. Push to `main` to deploy.
3. Test at the live GitHub Pages URL — do not run `streamlit`, `python -m http.server`, or other local servers.
4. For Supabase access rules, run `scripts/github_pages_supabase_policies.sql` in the Supabase SQL Editor.

### Test accounts

Portal users are Supabase Auth accounts registered in `admin_portal_users`:

- `umer@citihomes.ae` — Super User (full edit access)
- `test@citihomes.ae` — Viewer (read-only)

Passwords are managed in Supabase Authentication, not in this repo. Store them as Cursor secrets (e.g. `TEST_LOGIN_USERNAME` / `TEST_LOGIN_PASSWORD`) for automated login tests.

### Lint / test / build

No linter, test runner, or build command is configured for the static portal. Validation is manual: open the GitHub Pages URL, log in, and exercise a table page (e.g. Employee Master).

### Quick checks (no local runtime)

- **Portal live:** `curl -sI https://citi-homes.github.io/citi-homes-pc-admin/` → HTTP 200
- **Supabase:** use the anon key from `assets/supabase-config.js` against `https://xcddssirxwhywvhspica.supabase.co/rest/v1/`
