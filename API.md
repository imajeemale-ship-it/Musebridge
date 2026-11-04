# MuseBridge API

## Authentication

Local development defaults to demo headers. For production, set
`MUSEBRIDGE_AUTH_MODE=supabase` and send `Authorization: Bearer <access-token>`.
The API validates that token through Supabase Auth and never trusts a client-supplied user ID.
The browser client sends a token from `window.MUSEBRIDGE_ACCESS_TOKEN` or
`localStorage.musebridge_access_token` when present; otherwise it remains in demo mode.

Install dependencies with `python3 -m pip install -r requirements.txt`, then run:

```bash
uvicorn api:app --reload
```

For deployment, set `MUSEBRIDGE_AUTH_MODE=supabase` and add the deployed
frontend URL to `MUSEBRIDGE_ALLOWED_ORIGINS`.

The included `render.yaml` deploys the API and browser client as one Render
web service. Set the Supabase URL, publishable key, and deployed service URL
in Render environment variables before the first production test.

The API exposes health, consent grant/revoke, message prepare/approve/deliver, agreement approval, and audit routes. The local API uses SQLite (`musebridge.db`) so state survives process restarts. Protected routes require `X-Muse-User` and `X-Muse-Token`. Demo tokens are `alex-demo-token` and `jordan-demo-token`; replace them through `MUSEBRIDGE_ALEX_TOKEN` and `MUSEBRIDGE_JORDAN_TOKEN` before deployment. This is portfolio authentication, not production identity management.
