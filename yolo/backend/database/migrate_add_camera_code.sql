-- Add human-readable camera_code for CCTV Master sync (CAM-01, CAM-02, ...)
ALTER TABLE cameras ADD COLUMN IF NOT EXISTS camera_code VARCHAR(50);

WITH numbered AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY created_at, name) AS rn
    FROM cameras
    WHERE camera_code IS NULL OR camera_code = ''
)
UPDATE cameras c
SET camera_code = 'CAM-' || LPAD(n.rn::text, 2, '0')
FROM numbered n
WHERE c.id = n.id;

ALTER TABLE cameras ALTER COLUMN camera_code SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_cameras_camera_code ON cameras(camera_code);
