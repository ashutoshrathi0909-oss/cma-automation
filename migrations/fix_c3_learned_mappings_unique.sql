    -- Fix C3: Add unique constraint to learned_mappings table
    -- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New query)
    -- Prevents duplicate entries and stops the 500 error on correction submissions

    CREATE UNIQUE INDEX IF NOT EXISTS ux_learned_mappings
    ON learned_mappings (source_text, cma_field_name, industry_type);

    -- Verify: should show the new index
    SELECT indexname, indexdef
    FROM pg_indexes
    WHERE tablename = 'learned_mappings' AND indexname = 'ux_learned_mappings';
