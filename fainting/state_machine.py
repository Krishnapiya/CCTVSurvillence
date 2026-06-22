import logging
import time
import numpy as np
from config import settings
from posture import PostureState
from motion import calculate_vertical_velocity, verify_motionless

logger = logging.getLogger("fall_detection.state_machine")

class PersonState:
    def __init__(self, track_id: int):
        self.track_id = track_id
        
        # Histories: lists of (timestamp, value)
        self.posture_history: list[tuple[float, PostureState]] = []
        self.position_history: list[tuple[float, list, np.ndarray]] = []
        
        # State machine flags
        self.transition_detected = False
        self.transition_time = 0.0
        self.peak_downward_velocity = 0.0
        
        self.motionless_start_time = 0.0
        self.motionless_verified = False
        
        self.alert_triggered = False
        self.last_alert_time = 0.0
        
        # Keep track of when they became horizontal
        self.horizontal_start_time = 0.0

        # Displacement tracking to filter static objects (like chairs)
        self.start_position = None
        self.max_displacement = 0.0
        
        # Save the actual frame where the person was falling/horizontal
        self.last_falling_frame = None

    def add_frame(self, t: float, posture: PostureState, bbox: list, keypoints: np.ndarray, frame: np.ndarray = None):
        """
        Append a frame's worth of data to histories and trim old data.
        """
        self.posture_history.append((t, posture))
        self.position_history.append((t, bbox, keypoints))
        
        # Only store falling frame if the person has a history of being VERTICAL (to filter out static objects)
        has_vertical = any(pos == PostureState.VERTICAL for _, pos in self.posture_history)
        if posture in [PostureState.FALLING, PostureState.HORIZONTAL] and frame is not None and has_vertical:
            self.last_falling_frame = frame.copy()
            
        # Update displacement tracking
        center_x = (bbox[0] + bbox[2]) / 2.0
        center_y = (bbox[1] + bbox[3]) / 2.0
        current_pos = np.array([center_x, center_y])
        if self.start_position is None:
            self.start_position = current_pos
        else:
            displacement = float(np.linalg.norm(current_pos - self.start_position))
            if displacement > self.max_displacement:
                self.max_displacement = displacement

        # Limit history to 15 seconds to save memory
        cutoff = t - 15.0
        self.posture_history = [f for f in self.posture_history if f[0] >= cutoff]
        self.position_history = [f for f in self.position_history if f[0] >= cutoff]

class FallStateMachine:
    def __init__(self):
        """
        Initialize the fall detection state machine.
        """
        self.states: dict[int, PersonState] = {}

    def update(self, track_id: int, posture: PostureState, bbox: list, keypoints: np.ndarray, current_time: float = None, frame: np.ndarray = None) -> tuple[bool, float, dict]:
        """
        Update the state machine for a person in the current frame.
        
        Returns:
            A tuple of (trigger_alert, confidence_score, event_details)
        """
        if current_time is None:
            current_time = time.time()
            
        if track_id not in self.states:
            self.states[track_id] = PersonState(track_id)
            
        state = self.states[track_id]
        state.add_frame(current_time, posture, bbox, keypoints, frame)
        
        # 1. Cooldown Check
        if state.alert_triggered and (current_time - state.last_alert_time) < settings.ALERT_COOLDOWN:
            # We are in cooldown. Check if they have stood back up to reset state early (but keep cooldown timer active)
            if posture == PostureState.VERTICAL:
                state.transition_detected = False
                state.motionless_verified = False
            return False, 0.0, {}

        # If cooldown period has passed, reset alert_triggered
        if state.alert_triggered and (current_time - state.last_alert_time) >= settings.ALERT_COOLDOWN:
            state.alert_triggered = False
            state.transition_detected = False
            state.motionless_verified = False

        # 2. Velocity calculation
        v_y = calculate_vertical_velocity(state.position_history)
        logger.info(f"Track={track_id}, InstVelocity={v_y:.2f} px/s, PeakVelocity={state.peak_downward_velocity:.2f} px/s")
        
        # Track peak downward velocity during active motion
        if v_y > state.peak_downward_velocity:
            state.peak_downward_velocity = v_y

        # 3. Posture Transition State Machine
        if posture == PostureState.VERTICAL:
            # Person is standing up normally
            if state.transition_detected:
                logger.info(f"Person {track_id} stood back up. Resetting fall state.")
            state.transition_detected = False
            state.motionless_verified = False
            state.horizontal_start_time = 0.0
            state.motionless_start_time = 0.0
            state.peak_downward_velocity = 0.0
            
        elif posture == PostureState.HORIZONTAL:
            if state.horizontal_start_time == 0.0:
                state.horizontal_start_time = current_time
                if state.motionless_start_time == 0.0:
                    state.motionless_start_time = current_time
                
            # If not yet flagged as a transition, check history
            if not state.transition_detected:
                # Look back in the transition window (e.g. 3 seconds)
                window_start = current_time - settings.FALL_TRANSITION_WINDOW
                
                # Check if they were VERTICAL or FALLING within this window before becoming horizontal
                was_vertical = False
                for t_past, pos_past in state.posture_history:
                    if t_past >= window_start and t_past < state.horizontal_start_time:
                        if pos_past == PostureState.VERTICAL or pos_past == PostureState.FALLING:
                            was_vertical = True
                            break
                            
                if was_vertical:
                    state.transition_detected = True
                    state.transition_time = current_time
                    state.motionless_start_time = current_time
                    logger.info(f"Fall transition detected for person {track_id}! Starting motionless verification.")

            # Verify motionless status for any horizontal track
            if not state.motionless_verified:
                # How long have they been horizontal?
                horizontal_duration = current_time - state.motionless_start_time
                logger.info(f"Horizontal duration = {horizontal_duration:.2f}")
                
                if horizontal_duration >= settings.MOTIONLESS_TIME_THRESHOLD:
                    # Verify motionlessness over the last 5 seconds
                    is_motionless, motion_score = verify_motionless(state.position_history, settings.MOTIONLESS_TIME_THRESHOLD)
                    logger.info(
                        f"Alert Check | "
                        f"Track={track_id}, "
                        f"Velocity={state.peak_downward_velocity:.2f}/{settings.RAPID_FALL_VELOCITY_THRESHOLD}, "
                        f"Horizontal={horizontal_duration:.2f}/{settings.MOTIONLESS_TIME_THRESHOLD}, "
                        f"Motionless={is_motionless}"
                    )
                    
                    if is_motionless:
                        # Verify that this track has actually been VERTICAL in the past to filter out stationary background objects.
                        has_vertical = any(pos == PostureState.VERTICAL for _, pos in state.posture_history)
                        if not has_vertical:
                            logger.info(f"Ignoring static object track {track_id} (never seen in VERTICAL posture)")
                            state.motionless_start_time = current_time
                            return False, 0.0, {}
                            
                        # Verify velocity threshold
                        if state.peak_downward_velocity < settings.RAPID_FALL_VELOCITY_THRESHOLD:
                            logger.info(f"Ignoring track {track_id} due to low peak velocity ({state.peak_downward_velocity:.1f} px/s < {settings.RAPID_FALL_VELOCITY_THRESHOLD} px/s)")
                            state.motionless_start_time = current_time
                            return False, 0.0, {}
                            
                        state.motionless_verified = True
                        state.alert_triggered = True
                        state.last_alert_time = current_time
                        
                        # Calculate confidence score
                        # Base transition confidence
                        conf = 0.50
                        
                        # Add velocity factor (up to 0.25)
                        vel_ratio = min(1.0, state.peak_downward_velocity / settings.RAPID_FALL_VELOCITY_THRESHOLD)
                        vel_bonus = max(0.0, vel_ratio * 0.25)
                        conf += vel_bonus
                        
                        # Add motionless verification factor (0.25)
                        conf += 0.25
                        
                        # Bound to max 1.0
                        conf = min(1.0, conf)
                        
                        event_details = {
                            "track_id": track_id,
                            "peak_velocity": float(state.peak_downward_velocity),
                            "motion_score": float(motion_score),
                            "horizontal_duration": float(horizontal_duration)
                        }
                        
                        logger.warning(f"ALERT! Confirmed Fall/Fainting for person {track_id}. Confidence: {conf:.2f}")
                        return True, conf, event_details
                    else:
                        # If not motionless, we reset the motionless timer but KEEP the transition detected flag.
                        # This handles cases where they fall, move for a bit, then pass out/go still.
                        # We only want to trigger the alert when they stay still for 5 seconds.
                        # If they are moving a lot (e.g. struggling or crawling), the timer resets.
                        # Let's adjust motionless_start_time to current_time to wait another 5 seconds of still.
                        if motion_score < settings.MOTION_THRESHOLD * 2.0: # Moderate motion
                            # Do not reset completely, just delay slightly
                            pass
                        else:
                            # High motion, reset motionless start
                            state.motionless_start_time = current_time
                            
        return False, 0.0, {}

    def check_inactive_alerts(self, active_ids: set[int], current_time: float = None) -> list[tuple[int, float, dict, np.ndarray | None]]:
        """
        Check if any inactive (lost) tracks were falling/horizontal before they disappeared.
        If they have been lost for 2.0 seconds, trigger a faint alert!
        """
        if current_time is None:
            current_time = time.time()
            
        alerts = []
        for track_id, state in list(self.states.items()):
            if track_id not in active_ids:
                if state.alert_triggered:
                    continue
                    
                # Must have position history and posture history
                if not state.posture_history or not state.position_history:
                    continue
                    
                # Check if they had a FALLING or HORIZONTAL posture very recently before disappearing (within 1.5s of last seen)
                last_seen_time = state.position_history[-1][0]
                was_falling_or_horizontal_recently = False
                
                for t_past, pos_past in state.posture_history:
                    if pos_past in [PostureState.FALLING, PostureState.HORIZONTAL]:
                        if (last_seen_time - t_past) <= 1.5:
                            was_falling_or_horizontal_recently = True
                            break
                            
                if not was_falling_or_horizontal_recently:
                    continue
                    
                # Must have been VERTICAL at some point to ensure it's not a static object/furniture
                has_vertical = any(pos == PostureState.VERTICAL for _, pos in state.posture_history)
                if not has_vertical:
                    continue
                    
                # Verify that they had a rapid fall before disappearing
                if state.peak_downward_velocity < settings.RAPID_FALL_VELOCITY_THRESHOLD:
                    continue
                    
                # How long have they been lost?
                lost_duration = current_time - last_seen_time
                
                if lost_duration >= 2.0:
                    state.alert_triggered = True
                    state.last_alert_time = current_time
                    
                    event_details = {
                        "track_id": track_id,
                        "peak_velocity": float(state.peak_downward_velocity),
                        "lost_duration": float(lost_duration),
                        "faint_reason": "Track lost after fall/lying down"
                    }
                    logger.warning(f"ALERT! Confirmed Fall/Fainting for lost person {track_id} (lost for {lost_duration:.1f}s after fall/lying down). Confidence: 0.90")
                    alerts.append((track_id, 0.90, event_details, state.last_falling_frame))
        return alerts

    def clean_inactive_tracks(self, active_ids: set[int]):
        """
        Remove tracking history for IDs that have disappeared to prevent memory leaks.
        Only delete if they have been inactive for some time (e.g. 30 seconds).
        """
        current_time = time.time()
        ids_to_remove = []
        
        for track_id, state in list(self.states.items()):
            if track_id not in active_ids:
                # If there's position history, check when the last frame was added
                if state.position_history:
                    last_seen = state.position_history[-1][0]
                    if (current_time - last_seen) > 30.0:
                        ids_to_remove.append(track_id)
                else:
                    ids_to_remove.append(track_id)
                    
        for track_id in ids_to_remove:
            logger.info(f"Removing inactive state history for person {track_id}")
            del self.states[track_id]
