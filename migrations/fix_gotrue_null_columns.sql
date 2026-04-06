-- Fix GoTrue NULL column issue
--
-- Problem: When users are created via raw SQL INSERT into auth.users,
-- string columns like email_change can be left as NULL. GoTrue (Go code)
-- can't scan NULL into a Go `string` type, causing 500 errors:
-- "Database error querying schema"
--
-- Applied: 2026-04-04
-- Status: COALESCE UPDATE applied successfully. ALTER TABLE DEFAULT failed
--         (Supabase does not allow ALTER on auth.users — owned by supabase_auth_admin).
--
-- IMPORTANT: This fix must be re-run whenever users are created via raw SQL INSERT.
-- Always use Supabase Auth API (supabase.auth.admin.createUser) to avoid this issue.

-- Step 1: Fix existing NULL values (idempotent — safe to re-run)
UPDATE auth.users SET
  email_change = COALESCE(email_change, ''),
  phone_change = COALESCE(phone_change, ''),
  email_change_token_new = COALESCE(email_change_token_new, ''),
  email_change_token_current = COALESCE(email_change_token_current, ''),
  phone_change_token = COALESCE(phone_change_token, ''),
  reauthentication_token = COALESCE(reauthentication_token, ''),
  confirmation_token = COALESCE(confirmation_token, ''),
  recovery_token = COALESCE(recovery_token, '');

-- Step 2: Prevent future NULLs via DEFAULT constraints
-- NOTE: This will FAIL on Supabase hosted because auth.users is owned by
-- supabase_auth_admin. Kept here for documentation / self-hosted instances.
--
-- ALTER TABLE auth.users
--   ALTER COLUMN email_change SET DEFAULT '',
--   ALTER COLUMN phone_change SET DEFAULT '',
--   ALTER COLUMN email_change_token_new SET DEFAULT '',
--   ALTER COLUMN email_change_token_current SET DEFAULT '',
--   ALTER COLUMN phone_change_token SET DEFAULT '',
--   ALTER COLUMN reauthentication_token SET DEFAULT '';

-- Step 3: Verify — all string columns should show '' not NULL
SELECT id, email, email_change, phone_change, confirmation_token, recovery_token,
  email_change_token_new, email_change_token_current,
  phone_change_token, reauthentication_token
FROM auth.users;
