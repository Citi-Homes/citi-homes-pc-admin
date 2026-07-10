# Attendance Portal SSO setup

This HRMS now creates a short-lived signed launch URL for Admin users. It does not store or expose the Attendance Portal admin password.

## HRMS side

1. Copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml`.
2. Replace `attendance_sso.shared_secret` with a long random secret.
3. Use the same secret in the Attendance Portal server-side verifier.

## Attendance Portal side

The portal should read these query parameters:

- `sso_email`
- `sso_name`
- `sso_role`
- `sso_exp`
- `sso_nonce`
- `sso_sig`

Do not verify the signature in public browser JavaScript because that would expose the shared secret. Send the parameters to a Supabase Edge Function or another backend endpoint. The backend should:

1. Rebuild the payload from all `sso_*` parameters except `sso_sig`, sorted by key.
2. Verify `sso_sig` with HMAC-SHA256 and the shared secret.
3. Reject expired tokens using `sso_exp`.
4. Reject non-admin roles if only HRMS Admins may access admin attendance.
5. Create or return a Supabase session for the attendance portal.

Until the portal verifier is added, the HRMS will still open the Attendance Portal normally.
