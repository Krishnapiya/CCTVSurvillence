-- Reset sync tracking on station DB so events/clips are pushed again to master.
-- Run on the surveillance station PostgreSQL database.

BEGIN;
UPDATE events SET master_synced_at = NULL, master_clip_synced_at = NULL;
COMMIT;
