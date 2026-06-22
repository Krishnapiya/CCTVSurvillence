-- Add roi_name to events for CCTV Master sync (roi_name in master EventBase)
ALTER TABLE events ADD COLUMN IF NOT EXISTS roi_name VARCHAR(255);
