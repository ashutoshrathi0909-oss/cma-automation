-- Phase 8: User management — add is_active to user_profiles
-- Run this in Supabase SQL editor before deploying Phase 8.

ALTER TABLE user_profiles
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

-- Index for active user queries
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_active
    ON user_profiles (is_active);

COMMENT ON COLUMN user_profiles.is_active IS
    'Phase 8: admin can deactivate a user to block login without deleting the record.';
