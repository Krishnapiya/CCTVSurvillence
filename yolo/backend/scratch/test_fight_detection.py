import numpy as np
import asyncio
from app.services.ai_engine import ai_engine

def test_fight_heuristics():
    print("Testing scale-invariant fight detection heuristics...")
    
    # 1. Simulate two people far apart (No Fight)
    box_a = [100, 100, 200, 400] # height = 300
    box_b = [500, 100, 600, 400] # height = 300
    
    kps_a = np.zeros((17, 2))
    kps_a[9] = [150, 250] # left wrist
    conf_a = np.zeros(17)
    conf_a[9] = 0.9
    
    kps_b = np.zeros((17, 2))
    kps_b[0] = [550, 120] # nose
    conf_b = np.zeros(17)
    conf_b[0] = 0.9
    
    events = ai_engine._detect_fight_from_poses(
        [kps_a, kps_b],
        [box_a, box_b],
        [conf_a, conf_b]
    )
    print(f"Test 1 (Far apart): Expected 0 events, Got: {len(events)}")
    assert len(events) == 0, "Test 1 failed!"
    
    # 2. Simulate two people close and physical contact (Fight Detected)
    box_b_close = [150, 100, 250, 400] # overlaps horizontally
    kps_b_close = np.zeros((17, 2))
    kps_b_close[0] = [155, 248] # nose very close to wrist of A (150, 250)
    conf_b_close = np.zeros(17)
    conf_b_close[0] = 0.9
    
    events = ai_engine._detect_fight_from_poses(
        [kps_a, kps_b_close],
        [box_a, box_b_close],
        [conf_a, conf_b_close]
    )
    print(f"Test 2 (Physical contact): Expected 1 event, Got: {len(events)}")
    assert len(events) == 1, "Test 2 failed!"
    print(f"Event output: {events[0]}")
    assert events[0]["type"] == "fight"
    
    print("All heuristic tests passed successfully!")

if __name__ == "__main__":
    test_fight_heuristics()
