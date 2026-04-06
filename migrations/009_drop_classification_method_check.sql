-- 009: Drop stale classification_method check constraint
--
-- The original constraint only allowed: fuzzy_match, ai_haiku, ai_sonnet, manual, learned
-- The 5-tier pipeline now writes: rule_*, rule_engine_*, scoped_v3, scoped_doubt, ai_openrouter
-- classification_method is internal (never user input), so no constraint needed.
--
-- Applied manually on 2026-04-02 via Supabase SQL Editor.
-- This migration file ensures the change is tracked in version control.

ALTER TABLE classifications
DROP CONSTRAINT IF EXISTS classifications_classification_method_check;
