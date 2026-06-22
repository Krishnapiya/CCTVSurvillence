-- Track CCTV Master sync state on local events
ALTER TABLE events ADD COLUMN IF NOT EXISTS master_synced_at TIMESTAMPTZ;
ALTER TABLE events ADD COLUMN IF NOT EXISTS master_clip_synced_at TIMESTAMPTZ;
