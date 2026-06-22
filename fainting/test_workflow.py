import logging
import sys
import time
import numpy as np
import cv2
from config import settings
import database
from posture import analyze_posture, PostureState
from state_machine import FallStateMachine
from alert import trigger_alert

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("fall_detection.test_workflow")

def create_mock_keypoints(pose_type: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Creates mock keypoints for a person based on pose_type:
    'standing' (vertical) or 'lying' (horizontal).
    """
    # 17 keypoints of form [x, y]
    kp = np.zeros((17, 2), dtype=np.float32)
    kp_conf = np.ones(17, dtype=np.float32) # High confidence
    
    if pose_type == 'standing':
        # Shoulders (index 5, 6) above hips (index 11, 12)
        kp[5] = [200, 150] # Left shoulder
        kp[6] = [220, 150] # Right shoulder
        kp[11] = [200, 300] # Left hip
        kp[12] = [220, 300] # Right hip
    elif pose_type == 'lying':
        # Shoulders aligned horizontally with hips
        kp[5] = [150, 400] # Left shoulder
        kp[6] = [150, 420] # Right shoulder
        kp[11] = [350, 400] # Left hip
        kp[12] = [350, 420] # Right hip
    elif pose_type == 'transition':
        # Tilted
        kp[5] = [180, 250]
        kp[6] = [200, 250]
        kp[11] = [280, 350]
        kp[12] = [300, 350]
        
    return kp, kp_conf

def run_tests():
    logger.info("==============================================")
    logger.info("  STARTING MOCK FALL DETECTION SYSTEM TESTS  ")
    logger.info("==============================================")
    
    # 1. Test Database Connection (should gracefully handle unavailability)
    logger.info("Step 1: Testing Database connection...")
    db_initialized = database.init_db()
    if db_initialized:
        logger.info("PostgreSQL is connected and initialized.")
    else:
        logger.info("PostgreSQL connection skipped. Fallback to in-memory mock is active.")

    # 2. Test Posture Engine
    logger.info("\nStep 2: Testing Posture Analysis Engine...")
    
    # Mock vertical pose
    bbox_vert = [190, 100, 230, 450] # Aspect ratio = 40/350 = 0.11 (Vertical)
    kp_vert, conf_vert = create_mock_keypoints('standing')
    state, angle, ar = analyze_posture(bbox_vert, kp_vert, conf_vert)
    logger.info(f"Mock standing posture output: State={state}, Angle={angle:.1f}deg, AR={ar:.2f}")
    assert state == PostureState.VERTICAL, "Standing pose should be VERTICAL"

    # Mock transition pose
    bbox_trans = [160, 200, 320, 380] # Aspect ratio = 160/180 = 0.88 (Tilted)
    kp_trans, conf_trans = create_mock_keypoints('transition')
    state, angle, ar = analyze_posture(bbox_trans, kp_trans, conf_trans)
    logger.info(f"Mock tilting posture output: State={state}, Angle={angle:.1f}deg, AR={ar:.2f}")
    assert state == PostureState.FALLING, "Tilted pose should be FALLING"

    # Mock lying pose
    bbox_horiz = [100, 380, 400, 440] # Aspect ratio = 300/60 = 5.0 (Horizontal)
    kp_horiz, conf_horiz = create_mock_keypoints('lying')
    state, angle, ar = analyze_posture(bbox_horiz, kp_horiz, conf_horiz)
    logger.info(f"Mock lying posture output: State={state}, Angle={angle:.1f}deg, AR={ar:.2f}")
    assert state == PostureState.HORIZONTAL, "Lying pose should be HORIZONTAL"
    
    logger.info("Posture Analysis Engine passed.")

    # 3. Test State Machine & Motionless Verification Sequence
    logger.info("\nStep 3: Simulating Fall and Motionless Transition Sequence...")
    state_machine = FallStateMachine()
    
    track_id = 99
    simulated_fps = 10
    sim_delay = 1.0 / simulated_fps
    
    # Generate dummy frame for screenshot
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(dummy_frame, "TEST MOCK FRAME", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    
    video_buffer = []
    
    t_start = time.time()
    
    # Time 0.0s to 2.0s: Person is standing (VERTICAL)
    logger.info("1. Simulating standing state for 2 seconds...")
    for frame_idx in range(20):
        t_curr = t_start + frame_idx * sim_delay
        # Draw frame
        frame = dummy_frame.copy()
        cv2.putText(frame, f"Standing Frame {frame_idx}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        video_buffer.append(frame)
        
        triggered, conf, details = state_machine.update(
            track_id, PostureState.VERTICAL, bbox_vert, kp_vert, current_time=t_curr
        )
        assert not triggered, "Should not trigger alert while standing vertical"
    
    # Time 2.1s to 2.5s: Person falls down (rapid vertical movement)
    logger.info("2. Simulating rapid downward fall transition (FALLING -> HORIZONTAL)...")
    
    # We simulate a drop in height
    t_curr = t_start + 21 * sim_delay
    triggered, conf, details = state_machine.update(
        track_id, PostureState.FALLING, bbox_trans, kp_trans, current_time=t_curr
    )
    
    # Lying down posture begins
    t_curr = t_start + 22 * sim_delay
    triggered, conf, details = state_machine.update(
        track_id, PostureState.HORIZONTAL, bbox_horiz, kp_horiz, current_time=t_curr
    )
    logger.info("Lying down posture registered. Waiting 5s for motionless verification...")
    
    # Time 2.6s to 8.0s: Person remains horizontal and motionless
    # (motionless verification threshold = 5.0 seconds)
    alert_detected = False
    
    for frame_idx in range(23, 85):
        t_curr = t_start + frame_idx * sim_delay
        
        # Add frame to buffer
        frame = dummy_frame.copy()
        cv2.putText(frame, f"Horizontal Still Frame {frame_idx}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        video_buffer.append(frame)
        
        triggered, conf, details = state_machine.update(
            track_id, PostureState.HORIZONTAL, bbox_horiz, kp_horiz, current_time=t_curr
        )
        
        if triggered:
            logger.info(f"-> SUCCESS: Alert triggered at t + {t_curr - t_start:.2f}s with confidence: {conf:.2f}!")
            logger.info(f"Details: {details}")
            alert_detected = True
            
            # Execute mock trigger alert
            alert_data = trigger_alert(
                person_id=track_id,
                confidence=conf,
                annotated_frame=frame,
                video_frames=video_buffer[-100:], # Pass recent frames
                details=details
            )
            logger.info(f"Generated Event details: {alert_data}")
            # Wait briefly to let the background video writing thread finish
            logger.info("Waiting 2 seconds for the video writer thread to finish...")
            time.sleep(2.0)
            break
            
    assert alert_detected, "Alert should have been triggered after 5 seconds of motionlessness!"
    
    # 4. Verify API integration and Database Retrieval
    logger.info("\nStep 4: Verifying API data logging...")
    events = database.get_events()
    logger.info(f"Total events in log: {len(events)}")
    assert len(events) > 0, "Database should contain at least one logged event."
    
    latest = database.get_latest_event()
    logger.info(f"Latest logged event: {latest}")
    assert latest["person_id"] == track_id, "Latest logged event person_id should match simulated track ID"
    
    logger.info("\n==============================================")
    logger.info("  ALL TESTS PASSED SUCCESSFULLY!             ")
    logger.info("==============================================")

if __name__ == "__main__":
    run_tests()
