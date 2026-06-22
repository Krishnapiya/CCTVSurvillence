import logging
import numpy as np
from config import settings

logger = logging.getLogger("fall_detection.motion")

def calculate_vertical_velocity(position_history: list[tuple[float, list, np.ndarray]], window_size: float = 0.5) -> float:
    """
    Calculate the vertical velocity (downward movement speed) of a person.
    Uses the y-coordinate of the bounding box center.
    
    Args:
        position_history: List of (timestamp, bbox, keypoints)
        window_size: Time window in seconds to calculate velocity over
        
    Returns:
        Vertical velocity in pixels per second. Positive values mean downward movement.
    """
    if len(position_history) < 2:
        return 0.0
        
    # Get current state
    t_curr, bbox_curr, _ = position_history[-1]
    y_curr = (bbox_curr[1] + bbox_curr[3]) / 2.0  # Center Y
    
    # Find historical frame around window_size seconds ago
    target_time = t_curr - window_size
    past_frame = None
    
    for t_past, bbox_past, _ in reversed(position_history[:-1]):
        if t_past <= target_time:
            past_frame = (t_past, bbox_past)
            break
            
    # If no frame is old enough, use the oldest available
    if not past_frame:
        past_frame = (position_history[0][0], position_history[0][1])
        
    t_past, bbox_past = past_frame
    dt = t_curr - t_past
    
    if dt <= 0.001:
        return 0.0
        
    y_past = (bbox_past[1] + bbox_past[3]) / 2.0
    
    # Downward velocity (Y increases downwards in screen coordinates)
    velocity = (y_curr - y_past) / dt
    return velocity

def verify_motionless(position_history: list[tuple[float, list, np.ndarray]], duration: float = 5.0) -> tuple[bool, float]:
    """
    Verifies if a person has remained motionless over a certain duration.
    Calculates the standard deviation of the bounding box center position and keypoints.
    
    Args:
        position_history: List of (timestamp, bbox, keypoints)
        duration: Duration in seconds to analyze
        
    Returns:
        A tuple of (is_motionless, motion_score)
    """
    if len(position_history) < 2:
        return False, 999.0
        
    t_curr = position_history[-1][0]
    cutoff_time = t_curr - duration
    
    # Extract frames within the duration window
    window_frames = [f for f in position_history if f[0] >= cutoff_time]
    
    # We need frames spanning at least 70% of the requested duration to verify
    # We need frames spanning at least 70% of the requested duration to verify
    span = (t_curr - window_frames[0][0]) if window_frames else 0.0
    logger.info(
        f"Frames in history={len(window_frames)} "
        f"Span={span:.2f}s"
    )
    
    if not window_frames or span < (duration * 0.7):
        return False, 999.0
        
    centers_x = []
    centers_y = []
    
    for _, bbox, kp in window_frames:
        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0
        centers_x.append(cx)
        centers_y.append(cy)
        
    # Calculate standard deviation of center position
    std_x = np.std(centers_x)
    std_y = np.std(centers_y)
    motion_score = float(np.sqrt(std_x**2 + std_y**2))
    
    # Also verify that keypoints themselves aren't moving significantly
    # (e.g. waving hands or kicking legs while torso center is still)
    kp_movements = []
    for i in range(len(window_frames) - 1):
        kp_curr = window_frames[i+1][2]
        kp_prev = window_frames[i][2]
        # Ignore keypoints with zero coordinates (unseen)
        mask = (kp_curr[:, 0] > 0) & (kp_prev[:, 0] > 0)
        if np.any(mask):
            diff = kp_curr[mask] - kp_prev[mask]
            dist = np.linalg.norm(diff, axis=1)
            kp_movements.append(np.mean(dist))
            
    avg_kp_motion = np.mean(kp_movements) if kp_movements else 0.0
    
    # Combine bounding box motion and keypoint motion
    combined_score = motion_score + avg_kp_motion
    
    logger.info(f"Motion score={combined_score:.2f}")
    is_motionless = combined_score < settings.MOTION_THRESHOLD
    return is_motionless, combined_score
