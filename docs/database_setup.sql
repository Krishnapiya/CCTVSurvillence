-- Surveillance System Database Setup
-- PostgreSQL Schema with all tables, indexes, and initial data

-- Drop existing database if needed (for development)
-- DROP DATABASE IF EXISTS surveillance_db;
-- CREATE DATABASE surveillance_db;

-- Connect to the database
-- \c surveillance_db;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create user roles
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_read') THEN
      CREATE ROLE app_read;
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_write') THEN
      CREATE ROLE app_write;
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_admin') THEN
      CREATE ROLE app_admin;
   END IF;
END $$;

-- Create application user
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'surveillance_user') THEN

      CREATE ROLE surveillance_user LOGIN PASSWORD 'password';
   END IF;
END
$do$;

-- Grant permissions to roles
GRANT CONNECT ON DATABASE surveillance_system TO surveillance_user;
GRANT USAGE ON SCHEMA public TO surveillance_user;

-- ==================== TABLES ====================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'operator' CHECK (role IN ('admin', 'supervisor', 'operator', 'viewer')),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Camera profiles table
CREATE TABLE IF NOT EXISTS camera_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    camera_id VARCHAR(50) UNIQUE NOT NULL,
    dvr_connection_string VARCHAR(255) NOT NULL,
    rtsp_url VARCHAR(255),
    http_url VARCHAR(255),
    location VARCHAR(255),
    resolution VARCHAR(20) DEFAULT '1920x1080',
    fps INTEGER DEFAULT 30,
    status VARCHAR(20) DEFAULT 'inactive' CHECK (status IN ('active', 'inactive', 'error', 'maintenance')),
    is_recording BOOLEAN DEFAULT false,
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Event types table
CREATE TABLE IF NOT EXISTS event_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    default_voice_alert_path VARCHAR(255),
    default_color VARCHAR(7) DEFAULT '#FF0000',
    detection_algorithm VARCHAR(100),
    algorithm_parameters JSONB,
    is_system_defined BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ROIs table
CREATE TABLE IF NOT EXISTS rois (
    id SERIAL PRIMARY KEY,
    camera_profile_id INTEGER NOT NULL REFERENCES camera_profiles(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    polygon_coordinates JSONB NOT NULL,
    centroid_point POINT,
    area_square_pixels FLOAT,
    color VARCHAR(7) DEFAULT '#FF0000',
    fill_color VARCHAR(7) DEFAULT '#FF000030',
    stroke_width INTEGER DEFAULT 2,
    is_active BOOLEAN DEFAULT true,
    sensitivity FLOAT DEFAULT 0.5 CHECK (sensitivity >= 0 AND sensitivity <= 1),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ROI events table
CREATE TABLE IF NOT EXISTS roi_events (
    id SERIAL PRIMARY KEY,
    roi_id INTEGER NOT NULL REFERENCES rois(id) ON DELETE CASCADE,
    event_type_id INTEGER NOT NULL REFERENCES event_types(id),
    name VARCHAR(100),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    days_of_week JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    voice_alert_path VARCHAR(255),
    custom_alert_message TEXT,
    detection_threshold FLOAT DEFAULT 0.7 CHECK (detection_threshold >= 0 AND detection_threshold <= 1),
    cooldown_minutes INTEGER DEFAULT 5,
    max_alerts_per_hour INTEGER DEFAULT 10,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_roi_events_time_order CHECK (start_time < end_time),
    CONSTRAINT chk_roi_events_days_valid CHECK (jsonb_array_length(days_of_week) > 0)
);

-- Event logs table
CREATE TABLE IF NOT EXISTS event_logs (
    id BIGSERIAL PRIMARY KEY,
    roi_id INTEGER NOT NULL REFERENCES rois(id),
    event_type_id INTEGER NOT NULL REFERENCES event_types(id),
    camera_profile_id INTEGER NOT NULL REFERENCES camera_profiles(id),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    video_clip_path VARCHAR(500),
    thumbnail_path VARCHAR(500),
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    bounding_box JSONB,
    detection_metadata JSONB,
    alert_sent BOOLEAN DEFAULT false,
    alert_sent_at TIMESTAMP,
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    notes TEXT,
    false_positive BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alert queue table
CREATE TABLE IF NOT EXISTS alert_queue (
    id BIGSERIAL PRIMARY KEY,
    event_log_id BIGINT NOT NULL REFERENCES event_logs(id),
    alert_type VARCHAR(50) DEFAULT 'voice' CHECK (alert_type IN ('voice', 'email', 'sms', 'push')),
    recipient VARCHAR(255),
    alert_content TEXT NOT NULL,
    voice_file_path VARCHAR(255),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'sent', 'failed', 'cancelled')),
    scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System settings table
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    data_type VARCHAR(20) DEFAULT 'string' CHECK (data_type IN ('string', 'integer', 'boolean', 'json')),
    is_encrypted BOOLEAN DEFAULT false,
    category VARCHAR(50) DEFAULT 'general',
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DVR configurations table
CREATE TABLE IF NOT EXISTS dvr_configurations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    dvr_type VARCHAR(50) NOT NULL,
    connection_string VARCHAR(255) NOT NULL,
    api_port INTEGER,
    username VARCHAR(100),
    password_encrypted TEXT,
    max_connections INTEGER DEFAULT 10,
    timeout_seconds INTEGER DEFAULT 30,
    is_active BOOLEAN DEFAULT true,
    health_check_interval INTEGER DEFAULT 60,
    last_health_check TIMESTAMP,
    health_status VARCHAR(20) DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'unhealthy', 'unknown')),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Video storage configuration table
CREATE TABLE IF NOT EXISTS video_storage_config (
    id SERIAL PRIMARY KEY,
    storage_type VARCHAR(50) DEFAULT 'local' CHECK (storage_type IN ('local', 's3', 'azure', 'gcs')),
    base_path VARCHAR(500),
    access_key_encrypted TEXT,
    secret_key_encrypted TEXT,
    bucket_name VARCHAR(255),
    region VARCHAR(100),
    endpoint_url VARCHAR(500),
    retention_days INTEGER DEFAULT 30,
    max_storage_gb INTEGER,
    compression_enabled BOOLEAN DEFAULT true,
    compression_quality INTEGER DEFAULT 70 CHECK (compression_quality >= 1 AND compression_quality <= 100),
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    record_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System metrics table
CREATE TABLE IF NOT EXISTS system_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(50),
    tags JSONB,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== INDEXES ====================

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Camera profiles table indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_camera_profiles_camera_id ON camera_profiles(camera_id);
CREATE INDEX IF NOT EXISTS idx_camera_profiles_status ON camera_profiles(status);
CREATE INDEX IF NOT EXISTS idx_camera_profiles_created_by ON camera_profiles(created_by);
CREATE INDEX IF NOT EXISTS idx_camera_profiles_location ON camera_profiles(location);

-- Event types table indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_event_types_name ON event_types(name);
CREATE INDEX IF NOT EXISTS idx_event_types_category ON event_types(category);
CREATE INDEX IF NOT EXISTS idx_event_types_severity ON event_types(severity);
CREATE INDEX IF NOT EXISTS idx_event_types_is_active ON event_types(is_active);

-- ROIs table indexes
CREATE INDEX IF NOT EXISTS idx_rois_camera_profile_id ON rois(camera_profile_id);
CREATE INDEX IF NOT EXISTS idx_rois_is_active ON rois(is_active);
CREATE INDEX IF NOT EXISTS idx_rois_created_by ON rois(created_by);
CREATE INDEX IF NOT EXISTS idx_rois_centroid ON rois USING GIST(centroid_point);

-- ROI events table indexes
CREATE INDEX IF NOT EXISTS idx_roi_events_roi_id ON roi_events(roi_id);
CREATE INDEX IF NOT EXISTS idx_roi_events_event_type_id ON roi_events(event_type_id);
CREATE INDEX IF NOT EXISTS idx_roi_events_is_active ON roi_events(is_active);
CREATE INDEX IF NOT EXISTS idx_roi_events_time_range ON roi_events(start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_roi_events_days_of_week ON roi_events USING GIN(days_of_week);
CREATE INDEX IF NOT EXISTS idx_roi_events_created_by ON roi_events(created_by);

-- Event logs table indexes
CREATE INDEX IF NOT EXISTS idx_event_logs_roi_id ON event_logs(roi_id);
CREATE INDEX IF NOT EXISTS idx_event_logs_event_type_id ON event_logs(event_type_id);
CREATE INDEX IF NOT EXISTS idx_event_logs_camera_profile_id ON event_logs(camera_profile_id);
CREATE INDEX IF NOT EXISTS idx_event_logs_detected_at ON event_logs(detected_at);
CREATE INDEX IF NOT EXISTS idx_event_logs_alert_sent ON event_logs(alert_sent);
CREATE INDEX IF NOT EXISTS idx_event_logs_acknowledged_by ON event_logs(acknowledged_by);
CREATE INDEX IF NOT EXISTS idx_event_logs_false_positive ON event_logs(false_positive);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_event_logs_roi_detected ON event_logs(roi_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_event_logs_camera_detected ON event_logs(camera_profile_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_event_logs_type_detected ON event_logs(event_type_id, detected_at DESC);

-- Alert queue table indexes
CREATE INDEX IF NOT EXISTS idx_alert_queue_status ON alert_queue(status);
CREATE INDEX IF NOT EXISTS idx_alert_queue_priority ON alert_queue(priority);
CREATE INDEX IF NOT EXISTS idx_alert_queue_scheduled_at ON alert_queue(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_alert_queue_event_log_id ON alert_queue(event_log_id);

-- System settings table indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(key);
CREATE INDEX IF NOT EXISTS idx_system_settings_category ON system_settings(category);

-- DVR configurations table indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_dvr_configurations_name ON dvr_configurations(name);
CREATE INDEX IF NOT EXISTS idx_dvr_configurations_type ON dvr_configurations(dvr_type);
CREATE INDEX IF NOT EXISTS idx_dvr_configurations_is_active ON dvr_configurations(is_active);

-- Video storage config table indexes
CREATE INDEX IF NOT EXISTS idx_video_storage_config_type ON video_storage_config(storage_type);
CREATE INDEX IF NOT EXISTS idx_video_storage_config_is_active ON video_storage_config(is_active);

-- Audit logs table indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_table_name ON audit_logs(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_session_id ON audit_logs(session_id);

-- System metrics table indexes
CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_collected_at ON system_metrics(collected_at);
CREATE INDEX IF NOT EXISTS idx_system_metrics_tags ON system_metrics USING GIN(tags);

-- ==================== TRIGGERS ====================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update timestamp triggers
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_camera_profiles_updated_at 
    BEFORE UPDATE ON camera_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_event_types_updated_at 
    BEFORE UPDATE ON event_types 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rois_updated_at 
    BEFORE UPDATE ON rois 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roi_events_updated_at 
    BEFORE UPDATE ON roi_events 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at 
    BEFORE UPDATE ON system_settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dvr_configurations_updated_at 
    BEFORE UPDATE ON dvr_configurations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_video_storage_config_updated_at 
    BEFORE UPDATE ON video_storage_config 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ROI centroid calculation trigger
CREATE OR REPLACE FUNCTION calculate_roi_centroid()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate centroid from polygon coordinates
    IF NEW.polygon_coordinates IS NOT NULL AND jsonb_array_length(NEW.polygon_coordinates) > 0 THEN
        -- Simple centroid calculation (average of all points)
        NEW.centroid_point = POINT(
            AVG((coord->>'x')::FLOAT),
            AVG((coord->>'y')::FLOAT)
        ) FROM jsonb_array_elements(NEW.polygon_coordinates) AS coord;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_centroid_on_insert
    BEFORE INSERT ON rois
    FOR EACH ROW EXECUTE FUNCTION calculate_roi_centroid();

CREATE TRIGGER calculate_centroid_on_update
    BEFORE UPDATE ON rois
    FOR EACH ROW EXECUTE FUNCTION calculate_roi_centroid();

-- ==================== VIEWS ====================

-- Active camera ROIs with events view
CREATE OR REPLACE VIEW active_camera_rois AS
SELECT 
    cp.id as camera_id,
    cp.name as camera_name,
    cp.status as camera_status,
    r.id as roi_id,
    r.name as roi_name,
    r.polygon_coordinates,
    r.centroid_point,
    r.area_square_pixels,
    r.color,
    r.sensitivity,
    re.id as roi_event_id,
    re.event_type_id,
    et.name as event_type_name,
    et.severity as event_severity,
    re.start_time,
    re.end_time,
    re.days_of_week,
    re.detection_threshold,
    re.cooldown_minutes
FROM camera_profiles cp
JOIN rois r ON r.camera_profile_id = cp.id AND r.is_active = true
JOIN roi_events re ON re.roi_id = r.id AND re.is_active = true
JOIN event_types et ON et.id = re.event_type_id AND et.is_active = true
WHERE cp.status = 'active';

-- Recent events summary view
CREATE OR REPLACE VIEW recent_events_summary AS
SELECT 
    el.id,
    el.detected_at,
    cp.name as camera_name,
    cp.location,
    r.name as roi_name,
    et.name as event_type_name,
    et.severity,
    el.confidence_score,
    el.alert_sent,
    u_ack.username as acknowledged_by,
    el.acknowledged_at,
    CASE 
        WHEN el.acknowledged_at IS NULL THEN 'pending'
        WHEN el.false_positive = true THEN 'false_positive'
        ELSE 'acknowledged'
    END as status
FROM event_logs el
JOIN camera_profiles cp ON cp.id = el.camera_profile_id
JOIN rois r ON r.id = el.roi_id
JOIN event_types et ON et.id = el.event_type_id
LEFT JOIN users u_ack ON u_ack.id = el.acknowledged_by
WHERE el.detected_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY el.detected_at DESC;

-- System health dashboard view
CREATE OR REPLACE VIEW system_health_dashboard AS
SELECT 
    'total_cameras' as metric,
    COUNT(*) as value
FROM camera_profiles
UNION ALL
SELECT 
    'active_cameras' as metric,
    COUNT(*) as value
FROM camera_profiles WHERE status = 'active'
UNION ALL
SELECT 
    'total_rois' as metric,
    COUNT(*) as value
FROM rois WHERE is_active = true
UNION ALL
SELECT 
    'active_events' as metric,
    COUNT(*) as value
FROM roi_events WHERE is_active = true
UNION ALL
SELECT 
    'events_today' as metric,
    COUNT(*) as value
FROM event_logs WHERE DATE(detected_at) = CURRENT_DATE
UNION ALL
SELECT 
    'pending_alerts' as metric,
    COUNT(*) as value
FROM alert_queue WHERE status = 'pending';

-- ==================== INITIAL DATA ====================

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, first_name, last_name, role) 
VALUES ('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx.LrUpG', 'System', 'Administrator', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Insert default event types
INSERT INTO event_types (name, description, category, severity, is_system_defined) VALUES
('Person Detection', 'Detects people in monitored areas', 'security', 'medium', true),
('Vehicle Detection', 'Detects vehicles in monitored areas', 'security', 'medium', true),
('Intrusion', 'Unauthorized person in restricted area', 'security', 'high', true),
('Loitering', 'Person remaining in area for extended time', 'security', 'medium', true),
('Abandoned Object', 'Object left unattended in sensitive area', 'security', 'high', true),
('Crowd Detection', 'Large group of people gathering', 'safety', 'medium', true),
('Violence Detection', 'Aggressive behavior or fighting', 'security', 'critical', true),
('Fire/Smoke Detection', 'Fire or smoke detected', 'safety', 'critical', true)
ON CONFLICT (name) DO NOTHING;

-- Insert default system settings
INSERT INTO system_settings (key, value, description, data_type, category) VALUES
('max_concurrent_streams', '10', 'Maximum concurrent video streams per user', 'integer', 'performance'),
('default_retention_days', '30', 'Default video retention period in days', 'integer', 'storage'),
('alert_cooldown_seconds', '60', 'Minimum time between same type alerts', 'integer', 'alerts'),
('max_event_logs_per_page', '100', 'Maximum event logs to display per page', 'integer', 'ui'),
('enable_email_alerts', 'true', 'Enable email notifications', 'boolean', 'alerts'),
('system_timezone', 'UTC', 'System default timezone', 'string', 'general'),
('auto_cleanup_enabled', 'true', 'Enable automatic cleanup of old data', 'boolean', 'maintenance')
ON CONFLICT (key) DO NOTHING;

-- ==================== PERMISSIONS ====================

-- Grant permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON camera_profiles, rois, roi_events, event_logs, alert_queue TO surveillance_user;
GRANT SELECT, INSERT, UPDATE ON event_types, system_settings, dvr_configurations, video_storage_config TO surveillance_user;
GRANT SELECT, INSERT ON audit_logs, system_metrics TO surveillance_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO surveillance_user;

-- Grant read permissions to app_read role
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_read;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_read;

-- Grant write permissions to app_write role
GRANT SELECT, INSERT, UPDATE ON camera_profiles, rois, roi_events, event_logs, alert_queue TO app_write;
GRANT SELECT, INSERT, UPDATE ON event_types, system_settings TO app_write;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_write;

-- Grant admin permissions to app_admin role
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_admin;

-- Assign roles to application user
GRANT app_write TO surveillance_user;

-- ==================== FUNCTIONS ====================

-- Function to check if event is active now
CREATE OR REPLACE FUNCTION is_event_active_now(roi_event_id INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    event_record roi_events%ROWTYPE;
    _current_time TIME;
    current_day INTEGER;
    day_check BOOLEAN;
BEGIN
    -- Get event configuration
    SELECT * INTO event_record FROM roi_events WHERE id = roi_event_id AND is_active = true;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Check time range
    _current_time := CURRENT_TIME;
    IF _current_time < event_record.start_time OR _current_time > event_record.end_time THEN
        RETURN FALSE;
    END IF;
    
    -- Check day of week
    current_day := EXTRACT(DOW FROM CURRENT_DATE);
    day_check := event_record.days_of_week ? current_day::text;
    
    RETURN day_check;
END;
$$ LANGUAGE plpgsql;

-- Function to validate polygon
CREATE OR REPLACE FUNCTION validate_roi_polygon(polygon_coords JSONB)
RETURNS BOOLEAN AS $$
DECLARE
    points_count INTEGER;
    first_point JSONB;
    last_point JSONB;
BEGIN
    -- Check if polygon has at least 3 points
    points_count := jsonb_array_length(polygon_coords);
    IF points_count < 3 THEN
        RETURN FALSE;
    END IF;
    
    -- Additional validation can be added here
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old event logs
CREATE OR REPLACE FUNCTION cleanup_old_event_logs(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete old event logs
    DELETE FROM event_logs 
    WHERE detected_at < CURRENT_DATE - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log the cleanup
    INSERT INTO audit_logs (action, table_name, old_values)
    VALUES ('cleanup', 'event_logs', jsonb_build_object('deleted_count', deleted_count, 'retention_days', retention_days));
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ==================== FINAL SETUP ====================

-- Create indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_rois_polygon_gin ON rois USING GIN(polygon_coordinates);
CREATE INDEX IF NOT EXISTS idx_event_logs_metadata_gin ON event_logs USING GIN(detection_metadata);
CREATE INDEX IF NOT EXISTS idx_system_metrics_tags_gin ON system_metrics USING GIN(tags);

-- Create partial indexes for better performance
CREATE INDEX IF NOT EXISTS idx_rois_active_camera ON rois(camera_profile_id) WHERE is_active = true;
-- CREATE INDEX IF NOT EXISTS idx_event_logs_recent ON event_logs(detected_at DESC) WHERE detected_at > CURRENT_DATE - INTERVAL '30 days';
CREATE INDEX IF NOT EXISTS idx_alert_queue_pending ON alert_queue(scheduled_at) WHERE status = 'pending';

-- Vacuum analyze for better query planning
VACUUM ANALYZE;

-- Output setup completion message
DO $$
BEGIN
    RAISE NOTICE 'Surveillance system database setup completed successfully!';
    RAISE NOTICE 'Default admin user: admin / admin123';
    RAISE NOTICE 'Remember to change the default password in production!';
END $$;
