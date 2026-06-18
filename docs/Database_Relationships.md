# Database Relationships and Foreign Keys - Detailed Explanation

## 1. Overview of Database Relationships

This document provides a detailed explanation of how all tables in the surveillance system database are connected through foreign key relationships, with visual diagrams and detailed explanations of each relationship.

## 2. Relationship Diagram (Text-based)

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│    users    │    │camera_profiles│    │    rois     │    │  roi_events  │
├─────────────┤    ├──────────────┤    ├─────────────┤    ├──────────────┤
│ id (PK)     │────┤ id (PK)      │────┤ id (PK)     │────┤ id (PK)      │
│ username    │    │ name         │    │ camera_id   │    │ roi_id       │
│ email       │    │ camera_id    │    │ name        │    │ event_type_id│
│ password    │    │ dvr_string   │    │ polygon     │    │ start_time   │
│ role        │    │ rtsp_url     │    │ centroid    │    │ end_time     │
│ is_active   │    │ status       │    │ area        │    │ days_of_week │
│ created_at  │    │ created_by   │    │ color       │    │ is_active    │
│ updated_at  │    │ updated_at   │    │ is_active   │    │ created_by   │
└─────────────┘    │ location     │    │ sensitivity │    │ updated_at   │
                   │ resolution   │    │ created_by  │    └──────────────┘
                   │ fps          │    │ created_at  │           │
                   │ timezone     │    │ updated_at  │           │
                   └──────────────┘    └─────────────┘           │
                           │                   │               │
                           │                   │               │
                           └───────────────────┼───────────────┘
                                               │
                                               ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│event_types  │    │  event_logs  │    │alert_queue  │    │audit_logs    │
├─────────────┤    ├──────────────┤    ├──────────────┤    ├──────────────┤
│ id (PK)     │────┤ id (PK)      │    │ id (PK)     │    │ id (PK)      │
│ name        │    │ roi_id       │────┤ event_log_id│    │ user_id      │────┐
│ description │    │ event_type_id│────┤ alert_type  │    │ action       │   │
│ category    │    │ camera_id    │    │ recipient   │    │ table_name   │   │
│ severity    │    │ detected_at  │    │ content     │    │ record_id    │   │
│ voice_path  │    │ video_path   │    │ priority    │    │ old_values   │   │
│ algorithm   │    │ thumbnail    │    │ status      │    │ new_values   │   │
│ is_active   │    │ confidence   │    │ scheduled   │    │ ip_address   │   │
│ created_by  │    │ bounding_box │    │ sent_at     │    │ user_agent   │   │
│ created_at  │    │ metadata     │    │ error_msg   │    │ session_id   │   │
│ updated_at  │    │ alert_sent   │    │ retry_count│    │ created_at   │   │
└─────────────┘    │ acknowledged│    │ max_retries│    └──────────────┘
                   │ acknowledged│    │ created_at  │           │
                   │ notes        │    └──────────────┘           │
                   │ false_pos    │                                │
                   │ created_at   │                                │
                   └──────────────┘                                │
                           │                                       │
                           └───────────────────────────────────────┘
```

## 3. Detailed Foreign Key Relationships

### 3.1 users Table Relationships

#### Relationship: users → camera_profiles (One-to-Many)
```sql
-- In camera_profiles table:
created_by INTEGER REFERENCES users(id)

-- Explanation:
-- One user can create multiple camera profiles
-- Each camera profile has exactly one creator
-- This is a non-identifying relationship (camera_profile can exist without user after deletion)
-- ON DELETE: SET NULL (if user is deleted, created_by becomes NULL)
```

**Business Logic:**
- When a user creates a camera profile, their ID is stored in `camera_profiles.created_by`
- This helps track who created which cameras
- If a user is deleted, the camera profile remains but `created_by` becomes NULL

#### Relationship: users → rois (One-to-Many)
```sql
-- In rois table:
created_by INTEGER REFERENCES users(id)

-- Explanation:
-- One user can create multiple ROIs
-- Each ROI has exactly one creator
-- Non-identifying relationship
-- ON DELETE: SET NULL
```

#### Relationship: users → roi_events (One-to-Many)
```sql
-- In roi_events table:
created_by INTEGER REFERENCES users(id)

-- Explanation:
-- One user can create multiple ROI events
-- Each ROI event has exactly one creator
-- Non-identifying relationship
-- ON DELETE: SET NULL
```

#### Relationship: users → event_types (One-to-Many)
```sql
-- In event_types table:
created_by INTEGER REFERENCES users(id)

-- Explanation:
-- One user can create multiple event types
-- Each event type has exactly one creator
-- Non-identifying relationship
-- ON DELETE: SET NULL
```

#### Relationship: users → audit_logs (One-to-Many)
```sql
-- In audit_logs table:
user_id INTEGER REFERENCES users(id)

-- Explanation:
-- One user can have multiple audit log entries
-- Each audit log entry belongs to exactly one user (or NULL for system actions)
-- Non-identifying relationship
-- ON DELETE: SET NULL
```

#### Relationship: users → event_logs (One-to-Many)
```sql
-- In event_logs table:
acknowledged_by INTEGER REFERENCES users(id)

-- Explanation:
-- One user can acknowledge multiple event logs
-- Each event log can be acknowledged by at most one user
-- Non-identifying relationship
-- ON DELETE: SET NULL
```

### 3.2 camera_profiles Table Relationships

#### Relationship: camera_profiles → rois (One-to-Many)
```sql
-- In rois table:
camera_profile_id INTEGER NOT NULL REFERENCES camera_profiles(id) ON DELETE CASCADE

-- Explanation:
-- One camera profile can have multiple ROIs
-- Each ROI belongs to exactly one camera profile
-- Identifying relationship (ROI cannot exist without camera profile)
-- ON DELETE: CASCADE (if camera is deleted, all its ROIs are also deleted)
```

**Business Logic:**
- When a camera profile is created, it starts with 0 ROIs
- Users can add multiple ROIs to each camera
- If a camera is deleted, all associated ROIs are automatically deleted
- This maintains data integrity - no orphan ROIs

#### Relationship: camera_profiles → event_logs (One-to-Many)
```sql
-- In event_logs table:
camera_profile_id INTEGER NOT NULL REFERENCES camera_profiles(id)

-- Explanation:
-- One camera profile can have multiple event logs
-- Each event log belongs to exactly one camera profile
-- Identifying relationship
-- ON DELETE: RESTRICT (prevent deletion of camera with event logs)
```

### 3.3 rois Table Relationships

#### Relationship: rois → roi_events (One-to-Many)
```sql
-- In roi_events table:
roi_id INTEGER NOT NULL REFERENCES rois(id) ON DELETE CASCADE

-- Explanation:
-- One ROI can have multiple events
-- Each ROI event belongs to exactly one ROI
-- Identifying relationship
-- ON DELETE: CASCADE (if ROI is deleted, all its events are deleted)
```

**Business Logic:**
- Each ROI can have multiple time-based events (morning, night, etc.)
- Each event is tied to a specific ROI
- If ROI is deleted, all associated events are deleted
- This prevents orphan events without valid ROIs

#### Relationship: rois → event_logs (One-to-Many)
```sql
-- In event_logs table:
roi_id INTEGER NOT NULL REFERENCES rois(id)

-- Explanation:
-- One ROI can have multiple event logs
-- Each event log belongs to exactly one ROI
-- Identifying relationship
-- ON DELETE: RESTRICT (prevent deletion of ROI with event logs)
```

### 3.4 event_types Table Relationships

#### Relationship: event_types → roi_events (One-to-Many)
```sql
-- In roi_events table:
event_type_id INTEGER NOT NULL REFERENCES event_types(id)

-- Explanation:
-- One event type can be used in multiple ROI events
-- Each ROI event uses exactly one event type
-- Identifying relationship
-- ON DELETE: RESTRICT (prevent deletion of event type used in ROI events)
```

**Business Logic:**
- Event types are reusable (e.g., "intrusion" can be used in multiple ROIs)
- Each ROI event specifies which type of event to detect
- Cannot delete an event type if it's being used in active ROI events

#### Relationship: event_types → event_logs (One-to-Many)
```sql
-- In event_logs table:
event_type_id INTEGER NOT NULL REFERENCES event_types(id)

-- Explanation:
-- One event type can have multiple event logs
-- Each event log belongs to exactly one event type
-- Identifying relationship
-- ON DELETE: RESTRICT (prevent deletion of event type with event logs)
```

### 3.5 roi_events Table Relationships

#### Relationship: roi_events → event_logs (One-to-Many)
```sql
-- In event_logs table:
-- No direct foreign key, but relationship exists through roi_id and event_type_id
-- Each event log is created based on an ROI event configuration

-- Explanation:
-- One ROI event configuration can generate multiple event logs
-- Each event log is generated by exactly one ROI event configuration
-- This is a logical relationship, not enforced by foreign key
```

### 3.6 event_logs Table Relationships

#### Relationship: event_logs → alert_queue (One-to-Many)
```sql
-- In alert_queue table:
event_log_id BIGINT NOT NULL REFERENCES event_logs(id)

-- Explanation:
-- One event log can generate multiple alerts (voice, email, SMS)
-- Each alert belongs to exactly one event log
-- Identifying relationship
-- ON DELETE: CASCADE (if event log is deleted, associated alerts are deleted)
```

**Business Logic:**
- When an event is detected, multiple alerts can be generated
- Each alert is tied to the specific event log entry
- If event log is deleted, all pending/failed alerts are cleaned up

## 4. Relationship Cardinality Summary

### 4.1 One-to-Many Relationships
| Parent Table | Child Table | Relationship | Delete Action |
|--------------|-------------|--------------|---------------|
| users | camera_profiles | 1 user → many cameras | SET NULL |
| users | rois | 1 user → many ROIs | SET NULL |
| users | roi_events | 1 user → many events | SET NULL |
| users | event_types | 1 user → many event types | SET NULL |
| users | audit_logs | 1 user → many audit logs | SET NULL |
| users | event_logs (acknowledged_by) | 1 user → many acknowledgments | SET NULL |
| camera_profiles | rois | 1 camera → many ROIs | CASCADE |
| camera_profiles | event_logs | 1 camera → many event logs | RESTRICT |
| rois | roi_events | 1 ROI → many events | CASCADE |
| rois | event_logs | 1 ROI → many event logs | RESTRICT |
| event_types | roi_events | 1 type → many ROI events | RESTRICT |
| event_types | event_logs | 1 type → many event logs | RESTRICT |
| event_logs | alert_queue | 1 log → many alerts | CASCADE |

### 4.2 Many-to-Many Relationships (Resolved)
There are no direct many-to-many relationships in this design. All relationships are resolved through junction tables or one-to-many relationships.

## 5. Referential Integrity Constraints

### 5.1 Cascade Delete Rules
```sql
-- These relationships use CASCADE DELETE:
-- camera_profiles → rois (delete camera, delete all ROIs)
-- rois → roi_events (delete ROI, delete all events)
-- event_logs → alert_queue (delete event log, delete all alerts)

-- Rationale: These are "owned" relationships where child records 
-- have no meaning without the parent
```

### 5.2 Restrict Delete Rules
```sql
-- These relationships use RESTRICT DELETE:
-- camera_profiles → event_logs (cannot delete camera with logs)
-- rois → event_logs (cannot delete ROI with logs)
-- event_types → roi_events (cannot delete type used in events)
-- event_types → event_logs (cannot delete type with logs)

-- Rationale: These relationships represent historical data that 
-- should be preserved for audit and analysis
```

### 5.3 Set Null Delete Rules
```sql
-- These relationships use SET NULL DELETE:
-- users → camera_profiles (delete user, camera remains but creator unknown)
-- users → rois (delete user, ROI remains but creator unknown)
-- users → roi_events (delete user, event remains but creator unknown)
-- users → event_types (delete user, type remains but creator unknown)
-- users → audit_logs (delete user, audit log remains but user unknown)
-- users → event_logs.acknowledged_by (delete user, acknowledgment remains)

-- Rationale: These are "created by" relationships where the 
-- business object should remain even if creator is deleted
```

## 6. Data Flow Examples

### 6.1 Creating a Complete Camera Setup
```sql
-- Step 1: Create user (if not exists)
INSERT INTO users (username, email, password_hash, role) 
VALUES ('admin', 'admin@example.com', 'hashed_password', 'admin');

-- Step 2: Create camera profile
INSERT INTO camera_profiles (name, camera_id, dvr_connection_string, created_by)
VALUES ('Front Door', 'CAM001', 'rtsp://192.168.1.100:554/stream', 1);

-- Step 3: Create ROI for camera
INSERT INTO rois (camera_profile_id, name, polygon_coordinates, created_by)
VALUES (1, 'Entrance Area', '[{"x":100,"y":100},{"x":200,"y":100},{"x":200,"y":200},{"x":100,"y":200},{"x":100,"y":100}]', 1);

-- Step 4: Create event type (if not exists)
INSERT INTO event_types (name, description, severity, created_by)
VALUES ('Intrusion Detection', 'Person entering restricted area', 'high', 1);

-- Step 5: Create ROI event with time schedule
INSERT INTO roi_events (roi_id, event_type_id, start_time, end_time, days_of_week, created_by)
VALUES (1, 1, '22:00', '06:00', '[0,1,2,3,4,5,6]', 1);
```

### 6.2 Event Detection and Alert Flow
```sql
-- Step 1: Event detected (system creates event log)
INSERT INTO event_logs (roi_id, event_type_id, camera_profile_id, confidence_score, video_clip_path)
VALUES (1, 1, 1, 0.85, '/clips/2024/01/15/CAM001_intrusion_20240115_233022.mp4');

-- Step 2: Alert queued for processing
INSERT INTO alert_queue (event_log_id, alert_type, recipient, alert_content, voice_file_path)
VALUES (1, 'voice', 'default', 'Intrusion detected at Front Door', '/alerts/intrusion_alert.mp3');

-- Step 3: User acknowledges event
UPDATE event_logs 
SET acknowledged_by = 1, acknowledged_at = CURRENT_TIMESTAMP, notes = 'False alarm - maintenance personnel'
WHERE id = 1;
```

## 7. Query Examples Using Relationships

### 7.1 Get All Active Events for a Camera
```sql
SELECT 
    cp.name as camera_name,
    cp.location,
    r.name as roi_name,
    et.name as event_type_name,
    et.severity,
    re.start_time,
    re.end_time,
    re.days_of_week
FROM camera_profiles cp
JOIN rois r ON r.camera_profile_id = cp.id AND r.is_active = true
JOIN roi_events re ON re.roi_id = r.id AND re.is_active = true
JOIN event_types et ON et.id = re.event_type_id AND et.is_active = true
WHERE cp.id = 1 AND cp.status = 'active'
ORDER BY r.name, re.start_time;
```

### 7.2 Get Event History with User Information
```sql
SELECT 
    el.detected_at,
    cp.name as camera_name,
    r.name as roi_name,
    et.name as event_type_name,
    el.confidence_score,
    el.alert_sent,
    u_ack.username as acknowledged_by,
    el.acknowledged_at,
    u_creator.username as event_creator
FROM event_logs el
JOIN camera_profiles cp ON cp.id = el.camera_profile_id
JOIN rois r ON r.id = el.roi_id
JOIN event_types et ON et.id = el.event_type_id
LEFT JOIN users u_ack ON u_ack.id = el.acknowledged_by
JOIN roi_events re ON re.roi_id = r.id AND re.event_type_id = el.event_type_id
JOIN users u_creator ON u_creator.id = re.created_by
WHERE el.detected_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY el.detected_at DESC;
```

### 7.3 Get User Activity Summary
```sql
SELECT 
    u.username,
    u.role,
    COUNT(DISTINCT cp.id) as cameras_created,
    COUNT(DISTINCT r.id) as rois_created,
    COUNT(DISTINCT re.id) as events_created,
    COUNT(DISTINCT el.id) as events_acknowledged,
    COUNT(DISTINCT al.id) as audit_entries
FROM users u
LEFT JOIN camera_profiles cp ON cp.created_by = u.id
LEFT JOIN rois r ON r.created_by = u.id
LEFT JOIN roi_events re ON re.created_by = u.id
LEFT JOIN event_logs el ON el.acknowledged_by = u.id
LEFT JOIN audit_logs al ON al.user_id = u.id
GROUP BY u.id, u.username, u.role
ORDER BY u.username;
```

## 8. Relationship Validation Rules

### 8.1 Business Rule Constraints
```sql
-- Constraint: ROI must belong to active camera
ALTER TABLE rois ADD CONSTRAINT chk_roi_active_camera
CHECK (
    EXISTS (
        SELECT 1 FROM camera_profiles cp 
        WHERE cp.id = camera_profile_id AND cp.status = 'active'
    )
);

-- Constraint: Event time range must be valid
ALTER TABLE roi_events ADD CONSTRAINT chk_event_time_range
CHECK (start_time < end_time);

-- Constraint: Days of week must contain valid values
ALTER TABLE roi_events ADD CONSTRAINT chk_days_of_week
CHECK (
    jsonb_array_length(days_of_week) > 0 AND
    NOT EXISTS (
        SELECT 1 FROM jsonb_array_elements(days_of_week) day
        WHERE (day::text)::INTEGER NOT IN (0,1,2,3,4,5,6)
    )
);

-- Constraint: Confidence score must be valid
ALTER TABLE event_logs ADD CONSTRAINT chk_confidence_score
CHECK (confidence_score >= 0 AND confidence_score <= 1);
```

### 8.2 Trigger-Based Validation
```sql
-- Trigger: Prevent deletion of camera with recent events
CREATE OR REPLACE FUNCTION prevent_camera_deletion_with_recent_events()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM event_logs 
        WHERE camera_profile_id = OLD.id 
        AND detected_at > CURRENT_DATE - INTERVAL '30 days'
    ) THEN
        RAISE EXCEPTION 'Cannot delete camera with events in last 30 days';
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_camera_deletion_trigger
    BEFORE DELETE ON camera_profiles
    FOR EACH ROW EXECUTE FUNCTION prevent_camera_deletion_with_recent_events();
```

## 9. Summary of Key Relationships

### 9.1 Primary Relationship Chains
1. **User → Camera → ROI → Events → Event Logs → Alerts**
   - Complete flow from user creation to alert generation
   - Each step maintains referential integrity

2. **User → Event Types → ROI Events → Event Logs**
   - Event type definition and usage flow
   - Ensures event types are properly categorized

3. **User → Audit Logs**
   - System activity tracking
   - Maintains complete audit trail

### 9.2 Critical Foreign Keys
| Foreign Key | Table | References | Importance |
|-------------|-------|------------|------------|
| camera_profile_id | rois | camera_profiles(id) | Links ROI to camera |
| roi_id | roi_events | rois(id) | Links events to ROI |
| event_type_id | roi_events | event_types(id) | Defines event type |
| event_log_id | alert_queue | event_logs(id) | Links alerts to events |
| created_by | multiple tables | users(id) | Tracks creators |

### 9.3 Data Integrity Guarantees
- **No orphan ROIs**: All ROIs must belong to a valid camera
- **No orphan events**: All ROI events must belong to valid ROI and event type
- **No orphan alerts**: All alerts must belong to valid event log
- **Complete audit trail**: All actions are tracked with user information
- **Historical preservation**: Event logs are protected from accidental deletion

This relationship design ensures data integrity while providing the flexibility needed for a sophisticated surveillance system with ROI-based event detection and alerting.
