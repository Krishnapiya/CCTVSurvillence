-- Create table for fall and fainting events
CREATE TABLE IF NOT EXISTS events (
    event_id SERIAL PRIMARY KEY,
    person_id INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    confidence_score DOUBLE PRECISION NOT NULL,
    screenshot_path VARCHAR(512),
    video_path VARCHAR(512),
    details JSONB
);

-- Index for querying by timestamp
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC);
