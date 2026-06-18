# Database Design Document - Surveillance System

## 1. Database Overview

### 1.1 Database Choice: PostgreSQL 13+
- **Rationale**: Strong JSON support, spatial capabilities, excellent performance for time-series data
- **Extensions**: PostGIS (for spatial operations), pg_trgm (for text search)
- **Character Set**: UTF-8
- **Collation**: en_US.UTF-8

### 1.2 Database Naming Conventions
- **Tables**: snake_case, plural
- **Columns**: snake_case
- **Indexes**: idx_table_column(s)
- **Foreign Keys**: fk_table_column
- **Constraints**: ck_table_condition

## 2. Complete Database Schema

### 2.1 Core Tables

#### users - System Users
```sql
CREATE TABLE users (
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

-- Indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
```

#### camera_profiles - Camera Configuration
```sql
CREATE TABLE camera_profiles (
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

-- Indexes
CREATE UNIQUE INDEX idx_camera_profiles_camera_id ON camera_profiles(camera_id);
CREATE INDEX idx_camera_profiles_status ON camera_profiles(status);
CREATE INDEX idx_camera_profiles_created_by ON camera_profiles(created_by);
CREATE INDEX idx_camera_profiles_location ON camera_profiles(location);
```

#### event_types - Configurable Event Types
```sql
CREATE TABLE event_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- 'security', 'safety', 'operational', 'custom'
    severity VARCHAR(20) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    default_voice_alert_path VARCHAR(255),
    default_color VARCHAR(7) DEFAULT '#FF0000',
    detection_algorithm VARCHAR(100), -- 'motion_detection', 'object_detection', 'custom'
    algorithm_parameters JSONB,
    is_system_defined BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE UNIQUE INDEX idx_event_types_name ON event_types(name);
CREATE INDEX idx_event_types_category ON event_types(category);
CREATE INDEX idx_event_types_severity ON event_types(severity);
CREATE INDEX idx_event_types_is_active ON event_types(is_active);
```

#### rois - Regions of Interest
```sql
CREATE TABLE rois (
    id SERIAL PRIMARY KEY,
    camera_profile_id INTEGER NOT NULL REFERENCES camera_profiles(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    polygon_coordinates JSONB NOT NULL, -- [{"x": 100, "y": 200}, {"x": 150, "y": 250}, ...]
    centroid_point POINT, -- Calculated center point for quick reference
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

-- Indexes
CREATE INDEX idx_rois_camera_profile_id ON rois(camera_profile_id);
CREATE INDEX idx_rois_is_active ON rois(is_active);
CREATE INDEX idx_rois_created_by ON rois(created_by);
CREATE INDEX idx_rois_centroid ON rois USING GIST(centroid_point);

-- PostGIS spatial index for polygon operations
CREATE INDEX idx_rois_polygon ON rois USING GIST(polygon_coordinates);
```

#### roi_events - Time-based Events within ROIs
```sql
CREATE TABLE roi_events (
    id SERIAL PRIMARY KEY,
    roi_id INTEGER NOT NULL REFERENCES rois(id) ON DELETE CASCADE,
    event_type_id INTEGER NOT NULL REFERENCES event_types(id),
    name VARCHAR(100),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    days_of_week JSONB NOT NULL, -- [1,2,3,4,5] for Mon-Fri, [0,6] for Sun-Sat
    is_active BOOLEAN DEFAULT true,
    voice_alert_path VARCHAR(255),
    custom_alert_message TEXT,
    detection_threshold FLOAT DEFAULT 0.7 CHECK (detection_threshold >= 0 AND detection_threshold <= 1),
    cooldown_minutes INTEGER DEFAULT 5, -- Minimum time between same alerts
    max_alerts_per_hour INTEGER DEFAULT 10,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_roi_events_time_order CHECK (start_time < end_time),
    CONSTRAINT chk_roi_events_days_valid CHECK (jsonb_array_length(days_of_week) > 0)
);

-- Indexes
CREATE INDEX idx_roi_events_roi_id ON roi_events(roi_id);
CREATE INDEX idx_roi_events_event_type_id ON roi_events(event_type_id);
CREATE INDEX idx_roi_events_is_active ON roi_events(is_active);
CREATE INDEX idx_roi_events_time_range ON roi_events(start_time, end_time);
CREATE INDEX idx_roi_events_days_of_week ON roi_events USING GIN(days_of_week);
CREATE INDEX idx_roi_events_created_by ON roi_events(created_by);
```

### 2.2 Event Processing Tables

#### event_logs - Detected Events History
```sql
CREATE TABLE event_logs (
    id BIGSERIAL PRIMARY KEY,
    roi_id INTEGER NOT NULL REFERENCES rois(id),
    event_type_id INTEGER NOT NULL REFERENCES event_types(id),
    camera_profile_id INTEGER NOT NULL REFERENCES camera_profiles(id),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    video_clip_path VARCHAR(500),
    thumbnail_path VARCHAR(500),
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    bounding_box JSONB, -- [{"x": 100, "y": 200, "width": 50, "height": 60}, ...]
    detection_metadata JSONB, -- Additional algorithm-specific data
    alert_sent BOOLEAN DEFAULT false,
    alert_sent_at TIMESTAMP,
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    notes TEXT,
    false_positive BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_event_logs_roi_id ON event_logs(roi_id);
CREATE INDEX idx_event_logs_event_type_id ON event_logs(event_type_id);
CREATE INDEX idx_event_logs_camera_profile_id ON event_logs(camera_profile_id);
CREATE INDEX idx_event_logs_detected_at ON event_logs(detected_at);
CREATE INDEX idx_event_logs_alert_sent ON event_logs(alert_sent);
CREATE INDEX idx_event_logs_acknowledged_by ON event_logs(acknowledged_by);
CREATE INDEX idx_event_logs_false_positive ON event_logs(false_positive);

-- Composite indexes for common queries
CREATE INDEX idx_event_logs_roi_detected ON event_logs(roi_id, detected_at DESC);
CREATE INDEX idx_event_logs_camera_detected ON event_logs(camera_profile_id, detected_at DESC);
CREATE INDEX idx_event_logs_type_detected ON event_logs(event_type_id, detected_at DESC);

-- Partitioning by month for better performance (optional for high volume)
-- CREATE TABLE event_logs_y2024m01 PARTITION OF event_logs
-- FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

#### alert_queue - Pending Alerts
```sql
CREATE TABLE alert_queue (
    id BIGSERIAL PRIMARY KEY,
    event_log_id BIGINT NOT NULL REFERENCES event_logs(id),
    alert_type VARCHAR(50) DEFAULT 'voice' CHECK (alert_type IN ('voice', 'email', 'sms', 'push')),
    recipient VARCHAR(255), -- Email, phone number, or device token
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

-- Indexes
CREATE INDEX idx_alert_queue_status ON alert_queue(status);
CREATE INDEX idx_alert_queue_priority ON alert_queue(priority);
CREATE INDEX idx_alert_queue_scheduled_at ON alert_queue(scheduled_at);
CREATE INDEX idx_alert_queue_event_log_id ON alert_queue(event_log_id);
```

### 2.3 System Configuration Tables

#### system_settings - Global Configuration
```sql
CREATE TABLE system_settings (
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

-- Indexes
CREATE UNIQUE INDEX idx_system_settings_key ON system_settings(key);
CREATE INDEX idx_system_settings_category ON system_settings(category);
```

#### dvr_configurations - DVR Connection Settings
```sql
CREATE TABLE dvr_configurations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    dvr_type VARCHAR(50) NOT NULL, -- 'hikvision', 'dahua', 'axis', 'generic'
    connection_string VARCHAR(255) NOT NULL,
    api_port INTEGER,
    username VARCHAR(100),
    password_encrypted TEXT, -- Encrypted password
    max_connections INTEGER DEFAULT 10,
    timeout_seconds INTEGER DEFAULT 30,
    is_active BOOLEAN DEFAULT true,
    health_check_interval INTEGER DEFAULT 60, -- seconds
    last_health_check TIMESTAMP,
    health_status VARCHAR(20) DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'unhealthy', 'unknown')),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE UNIQUE INDEX idx_dvr_configurations_name ON dvr_configurations(name);
CREATE INDEX idx_dvr_configurations_type ON dvr_configurations(dvr_type);
CREATE INDEX idx_dvr_configurations_is_active ON dvr_configurations(is_active);
```

#### video_storage_config - Storage Management
```sql
CREATE TABLE video_storage_config (
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

-- Indexes
CREATE INDEX idx_video_storage_config_type ON video_storage_config(storage_type);
CREATE INDEX idx_video_storage_config_is_active ON video_storage_config(is_active);
```

### 2.4 Audit and Logging Tables

#### audit_logs - System Audit Trail
```sql
CREATE TABLE audit_logs (
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

-- Indexes
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_table_name ON audit_logs(table_name);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_session_id ON audit_logs(session_id);
```

#### system_metrics - Performance Monitoring
```sql
CREATE TABLE system_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(50),
    tags JSONB, -- {"camera_id": "cam01", "type": "cpu"}
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX idx_system_metrics_collected_at ON system_metrics(collected_at);
CREATE INDEX idx_system_metrics_tags ON system_metrics USING GIN(tags);
```

## 3. Database Views

### 3.1 Active Camera ROIs with Events
```sql
CREATE VIEW active_camera_rois AS
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
```

### 3.2 Recent Events Summary
```sql
CREATE VIEW recent_events_summary AS
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
WHERE el.detected_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY el.detected_at DESC;
```

### 3.3 System Health Dashboard
```sql
CREATE VIEW system_health_dashboard AS
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
```

## 4. Stored Procedures and Functions

### 4.1 ROI Polygon Validation
```sql
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
    
    -- Check if polygon is closed (first point equals last point)
    first_point := jsonb_array_element(polygon_coords, 0);
    last_point := jsonb_array_element(polygon_coords, points_count - 1);
    
    IF first_point != last_point THEN
        RETURN FALSE;
    END IF;
    
    -- Additional validation can be added here
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
```

### 4.2 Event Time Check
```sql
CREATE OR REPLACE FUNCTION is_event_active_now(roi_event_id INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    event_record roi_events%ROWTYPE;
    current_time TIME;
    current_day INTEGER;
    day_check BOOLEAN;
BEGIN
    -- Get event configuration
    SELECT * INTO event_record FROM roi_events WHERE id = roi_event_id AND is_active = true;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Check time range
    current_time := CURRENT_TIME;
    IF current_time < event_record.start_time OR current_time > event_record.end_time THEN
        RETURN FALSE;
    END IF;
    
    -- Check day of week
    current_day := EXTRACT(DOW FROM CURRENT_DATE); -- 0=Sunday, 6=Saturday
    day_check := event_record.days_of_week ? current_day::text;
    
    RETURN day_check;
END;
$$ LANGUAGE plpgsql;
```

### 4.3 ROI Centroid Calculation
```sql
CREATE OR REPLACE FUNCTION calculate_roi_centroid(polygon_coords JSONB)
RETURNS POINT AS $$
DECLARE
    total_points INTEGER;
    sum_x FLOAT := 0;
    sum_y FLOAT := 0;
    point JSONB;
    i INTEGER;
BEGIN
    total_points := jsonb_array_length(polygon_coords) - 1; -- Exclude duplicate closing point
    
    FOR i IN 0..total_points-1 LOOP
        point := jsonb_array_element(polygon_coords, i);
        sum_x := sum_x + (point->>'x')::FLOAT;
        sum_y := sum_y + (point->>'y')::FLOAT;
    END LOOP;
    
    RETURN POINT(sum_x / total_points, sum_y / total_points);
END;
$$ LANGUAGE plpgsql;
```

### 4.4 Event Log Cleanup
```sql
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
```

## 5. Triggers

### 5.1 Update Timestamps
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to relevant tables
CREATE TRIGGER update_camera_profiles_updated_at 
    BEFORE UPDATE ON camera_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rois_updated_at 
    BEFORE UPDATE ON rois 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roi_events_updated_at 
    BEFORE UPDATE ON roi_events 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 5.2 Audit Logging
```sql
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    audit_action TEXT;
    old_data JSONB;
    new_data JSONB;
BEGIN
    IF TG_OP = 'DELETE' THEN
        audit_action := 'DELETE';
        old_data := to_jsonb(OLD);
        new_data := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        audit_action := 'UPDATE';
        old_data := to_jsonb(OLD);
        new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'INSERT' THEN
        audit_action := 'INSERT';
        old_data := NULL;
        new_data := to_jsonb(NEW);
    END IF;
    
    INSERT INTO audit_logs (action, table_name, record_id, old_values, new_values)
    VALUES (audit_action, TG_TABLE_NAME, COALESCE(NEW.id, OLD.id), old_data, new_data);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply to critical tables
CREATE TRIGGER audit_camera_profiles
    AFTER INSERT OR UPDATE OR DELETE ON camera_profiles
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_rois
    AFTER INSERT OR UPDATE OR DELETE ON rois
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_roi_events
    AFTER INSERT OR UPDATE OR DELETE ON roi_events
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
```

### 5.3 ROI Centroid Auto-Calculation
```sql
CREATE OR REPLACE FUNCTION calculate_roi_centroid_trigger()
RETURNS TRIGGER AS $$
BEGIN
    NEW.centroid_point = calculate_roi_centroid(NEW.polygon_coordinates);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_centroid_on_insert
    BEFORE INSERT ON rois
    FOR EACH ROW EXECUTE FUNCTION calculate_roi_centroid_trigger();

CREATE TRIGGER calculate_centroid_on_update
    BEFORE UPDATE ON rois
    FOR EACH ROW EXECUTE FUNCTION calculate_roi_centroid_trigger();
```

## 6. Database Indexes Optimization

### 6.1 Composite Indexes for Common Queries
```sql
-- Event logs with camera and time filtering
CREATE INDEX idx_event_logs_camera_time ON event_logs(camera_profile_id, detected_at DESC);

-- ROI events with active status and time filtering
CREATE INDEX idx_roi_events_active_time ON roi_events(is_active, start_time, end_time) WHERE is_active = true;

-- Alert queue processing
CREATE INDEX idx_alert_queue_status_priority ON alert_queue(status, priority, scheduled_at);

-- Audit logs for user activity
CREATE INDEX idx_audit_logs_user_time ON audit_logs(user_id, created_at DESC);
```

### 6.2 Partial Indexes for Performance
```sql
-- Only index active ROIs
CREATE INDEX idx_rois_active_camera ON rois(camera_profile_id) WHERE is_active = true;

-- Only index recent event logs
CREATE INDEX idx_event_logs_recent ON event_logs(detected_at DESC) WHERE detected_at > CURRENT_DATE - INTERVAL '30 days';

-- Only index pending alerts
CREATE INDEX idx_alert_queue_pending ON alert_queue(scheduled_at) WHERE status = 'pending';
```

### 6.3 GIN Indexes for JSONB Columns
```sql
-- ROI polygon coordinates for spatial queries
CREATE INDEX idx_rois_polygon_gin ON rois USING GIN(polygon_coordinates);

-- Event metadata filtering
CREATE INDEX idx_event_logs_metadata_gin ON event_logs USING GIN(detection_metadata);

-- System metrics tags
CREATE INDEX idx_system_metrics_tags_gin ON system_metrics USING GIN(tags);
```

## 7. Database Security

### 7.1 Row Level Security (RLS)
```sql
-- Enable RLS on sensitive tables
ALTER TABLE camera_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE rois ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_logs ENABLE ROW LEVEL SECURITY;

-- Policy for camera profiles based on user role
CREATE POLICY camera_profiles_policy ON camera_profiles
    FOR ALL
    USING (
        CASE 
            WHEN EXISTS(SELECT 1 FROM users WHERE id = current_setting('app.current_user_id')::INTEGER AND role = 'admin') THEN true
            WHEN created_by = current_setting('app.current_user_id')::INTEGER THEN true
            ELSE false
        END
    );

-- Policy for event logs (viewers can see, operators can acknowledge)
CREATE POLICY event_logs_policy ON event_logs
    FOR SELECT
    USING (
        EXISTS(
            SELECT 1 FROM users u 
            WHERE u.id = current_setting('app.current_user_id')::INTEGER 
            AND u.role IN ('admin', 'supervisor', 'operator', 'viewer')
        )
    );

CREATE POLICY event_logs_update_policy ON event_logs
    FOR UPDATE
    USING (
        EXISTS(
            SELECT 1 FROM users u 
            WHERE u.id = current_setting('app.current_user_id')::INTEGER 
            AND u.role IN ('admin', 'supervisor', 'operator')
        )
    );
```

### 7.2 Database Roles and Permissions
```sql
-- Application roles
CREATE ROLE app_read;
CREATE ROLE app_write;
CREATE ROLE app_admin;

-- Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_read;
GRANT SELECT, INSERT, UPDATE ON camera_profiles, rois, roi_events, event_logs TO app_write;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_admin;

-- Sequence permissions
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_write;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_admin;
```

## 8. Performance Monitoring and Maintenance

### 8.1 Performance Monitoring Queries
```sql
-- Slow query monitoring
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
WHERE mean_time > 1000 -- queries taking more than 1 second
ORDER BY mean_time DESC
LIMIT 10;

-- Index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 8.2 Maintenance Procedures
```sql
-- Scheduled maintenance function
CREATE OR REPLACE FUNCTION perform_maintenance()
RETURNS VOID AS $$
BEGIN
    -- Update table statistics
    ANALYZE;
    
    -- Clean up old event logs
    PERFORM cleanup_old_event_logs(90);
    
    -- Reindex fragmented indexes
    REINDEX INDEX CONCURRENTLY idx_event_logs_detected_at;
    
    -- Vacuum analyze
    VACUUM ANALYZE;
    
    -- Log maintenance
    INSERT INTO audit_logs (action, table_name)
    VALUES ('maintenance', 'system');
END;
$$ LANGUAGE plpgsql;
```

## 9. Backup and Recovery Strategy

### 9.1 Backup Configuration
```bash
# pg_backup.conf
[pg_backup]
# Database connection
db_host=localhost
db_port=5432
db_name=surveillance_db
db_user=backup_user

# Backup settings
backup_dir=/var/backups/postgresql
backup_retention_days=30
compression_level=6
parallel_jobs=4

# Schedule
full_backup_daily=true
incremental_backup_hourly=true
```

### 9.2 Point-in-Time Recovery Setup
```sql
-- Enable WAL archiving
-- postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'
max_wal_senders = 3
```

## 10. Migration Scripts

### 10.1 Initial Database Setup
```sql
-- 001_initial_schema.sql
-- This file contains all CREATE TABLE statements
-- Run this to create the initial database structure
```

### 10.2 Data Migration Example
```sql
-- 002_add_camera_location.sql
ALTER TABLE camera_profiles ADD COLUMN location VARCHAR(255);
UPDATE camera_profiles SET location = 'Unknown' WHERE location IS NULL;
ALTER TABLE camera_profiles ALTER COLUMN location SET NOT NULL;
```

This comprehensive database design provides:
- **Complete schema** with all necessary tables and relationships
- **Performance optimization** through strategic indexing
- **Security features** with RLS and proper permissions
- **Maintenance procedures** for ongoing database health
- **Scalability considerations** for high-volume event processing
- **Audit capabilities** for compliance and debugging

The design supports all your requirements for multi-camera ROI-based event detection with time-based scheduling and alerting.
