import logging
import math
from enum import Enum
import numpy as np
from config import settings

logger = logging.getLogger("fall_detection.posture")

class PostureState(str, Enum):
    VERTICAL = "VERTICAL"
    FALLING = "FALLING"
    HORIZONTAL = "HORIZONTAL"

def calculate_torso_angle(keypoints: np.ndarray, keypoints_conf: np.ndarray) -> float | None:
    """
    Calculates the angle of the body axis relative to the vertical axis.
    Uses all visible keypoints in the upper and lower body to be robust against occlusion.
    """
    conf_thresh = settings.POSE_KEYPOINT_CONFIDENCE
    
    # Upper body points (head, shoulders)
    upper_indices = [0, 1, 2, 3, 4, 5, 6]
    # Lower body points (hips, knees, ankles)
    lower_indices = [11, 12, 13, 14, 15, 16]
    
    upper_pts = []
    lower_pts = []
    
    for idx in upper_indices:
        if keypoints_conf[idx] >= conf_thresh:
            upper_pts.append(keypoints[idx])
            
    for idx in lower_indices:
        if keypoints_conf[idx] >= conf_thresh:
            lower_pts.append(keypoints[idx])
            
    # We need at least one upper body and one lower body point to calculate orientation
    if not upper_pts or not lower_pts:
        return None
        
    upper_avg = np.mean(upper_pts, axis=0)
    lower_avg = np.mean(lower_pts, axis=0)
    
    # Vector from lower body to upper body
    dx = upper_avg[0] - lower_avg[0]
    dy = upper_avg[1] - lower_avg[1]
    
    try:
        angle_rad = math.atan2(abs(dx), abs(dy))
        angle_deg = math.degrees(angle_rad)
        return angle_deg
    except Exception as e:
        logger.error(f"Error calculating body angle: {e}")
        return None

def is_person_on_floor(keypoints: np.ndarray, conf: np.ndarray) -> bool:
    visible = conf > 0.3
    if visible.sum() < 4:
        visible = conf > 0.15
        if visible.sum() < 4:
            return False
            
    y_values = keypoints[visible][:, 1]
    spread = np.max(y_values) - np.min(y_values)
    return spread < 120

def analyze_posture(bbox: list, keypoints: np.ndarray, keypoints_conf: np.ndarray, track_id = None) -> tuple[PostureState, float | None, float]:
    """
    Analyze the posture of a person based on body axis angle and bounding box aspect ratio.
    """
    x1, y1, x2, y2 = bbox
    width = max(1.0, x2 - x1)
    height = max(1.0, y2 - y1)
    aspect_ratio = width / height
    
    angle = calculate_torso_angle(keypoints, keypoints_conf)
    on_floor = is_person_on_floor(keypoints, keypoints_conf)
    
    # Check if the person is lying down vertically (head below hips or level with hips)
    is_vertical_lying = False
    conf_thresh = settings.POSE_KEYPOINT_CONFIDENCE
    
    # Upper body points (head, shoulders)
    upper_indices = [0, 1, 2, 3, 4, 5, 6]
    # Lower body points (hips, knees, ankles)
    lower_indices = [11, 12, 13, 14, 15, 16]
    
    upper_pts_y = [keypoints[idx][1] for idx in upper_indices if keypoints_conf[idx] >= conf_thresh]
    lower_pts_y = [keypoints[idx][1] for idx in lower_indices if keypoints_conf[idx] >= conf_thresh]
    
    if upper_pts_y and lower_pts_y:
        upper_avg_y = np.mean(upper_pts_y)
        lower_avg_y = np.mean(lower_pts_y)
        
        # If head/shoulders are below or level with hips/legs in the image (larger Y coordinate),
        # they are lying down (vertical lying down).
        if upper_avg_y >= lower_avg_y - 15.0:
            is_vertical_lying = True
            
    if angle is not None:
        # Use angle-based classification primarily
        if angle >= settings.FALL_ANGLE_THRESHOLD or is_vertical_lying or on_floor:
            # Lowered to 0.35 to support steep overhead camera angles
            if aspect_ratio > 0.35 or is_vertical_lying or on_floor:
                state = PostureState.HORIZONTAL
            else:
                state = PostureState.FALLING
        elif angle <= settings.VERTICAL_ANGLE_THRESHOLD:
            if on_floor:
                state = PostureState.HORIZONTAL
            else:
                state = PostureState.VERTICAL
        else:
            if on_floor:
                state = PostureState.HORIZONTAL
            else:
                state = PostureState.FALLING
    else:
        # Fall back to aspect ratio if keypoints are missing/not visible
        # Set to 0.45 to catch vertical-aligned lying down bodies
        if aspect_ratio > 0.45 or is_vertical_lying or on_floor:
            state = PostureState.HORIZONTAL
        else:
            state = PostureState.VERTICAL
            
    print(f"[FAINT DEBUG] Posture Analysis - Track={track_id}, Angle={f'{angle:.1f}' if angle is not None else 'None'}, Aspect={aspect_ratio:.2f}, OnFloor={on_floor}, VertLying={is_vertical_lying}, State={state}")
    logger.info(
        f"Track={track_id}, "
        f"Angle={f'{angle:.1f}' if angle is not None else 'None'}, "
        f"Aspect={aspect_ratio:.2f}, "
        f"State={state}"
    )
    return state, angle, aspect_ratio
