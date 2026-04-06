-- Migration: Create system worker user for ARQ audit logs
-- Problem: ARQ worker uses SYSTEM_USER_ID = '00000000-0000-0000-0000-000000000000'
--          for audit logging, but this UUID didn't exist in auth.users.
--          cma_report_history.performed_by has FK to auth.users(id), so
--          worker audit inserts silently failed (swallowed by try/except).
-- Fix:     Create the system user in auth.users and user_profiles.

-- 1. Create system user in auth.users
INSERT INTO auth.users (
  id, instance_id, aud, role, email,
  encrypted_password, email_confirmed_at,
  raw_app_meta_data, raw_user_meta_data,
  created_at, updated_at,
  confirmation_token, recovery_token
) VALUES (
  '00000000-0000-0000-0000-000000000000',
  '00000000-0000-0000-0000-000000000000',
  'authenticated', 'service_role',
  'system@cma-automation.internal',
  crypt('not-a-real-login', gen_salt('bf')),
  now(),
  '{"provider":"email","providers":["email"]}',
  '{"full_name":"System Worker"}',
  now(), now(),
  '', ''
)
ON CONFLICT (id) DO NOTHING;

-- 2. Create matching user_profiles entry
INSERT INTO public.user_profiles (id, full_name, role, created_at, updated_at)
VALUES (
  '00000000-0000-0000-0000-000000000000',
  'System Worker',
  'admin',
  now(), now()
)
ON CONFLICT (id) DO NOTHING;
