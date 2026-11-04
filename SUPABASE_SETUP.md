# Supabase production identity gate

The repository contains the production schema at `supabase/migrations/202611030001_musebridge_core.sql`.

It is applied to the `MuseBridge` project in the `Grabbit Portfolio` organization
(project ref `yvrwrgbokvzcmjjatqfx`). The dashboard verification returned 7 tables,
7 RLS-enabled tables, and 11 policies.

For a fresh environment:

1. Authenticate the Supabase CLI or connect the Supabase MCP server.
2. Confirm the target project reference.
3. Apply the migration through the project’s migration workflow.
4. Run a test query and RLS/advisor checks.
5. Replace the demo token dependency in `api.py` with verification of Supabase access tokens.

The migration uses `auth.uid()` and bridge membership rather than editable user metadata. It enables RLS on every exposed table and includes ownership checks for consent, message creation, and agreement approvals.
