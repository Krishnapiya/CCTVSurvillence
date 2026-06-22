import sys
fainting_dir = "/data/hfllama/survialance/fainting"
if fainting_dir not in sys.path:
    sys.path.insert(0, fainting_dir)

try:
    from tracker import PersonTracker
    print("Successfully imported PersonTracker")
except Exception as e:
    print(f"Failed to import PersonTracker: {e}")

try:
    from posture import analyze_posture, PostureState
    print("Successfully imported posture functions")
except Exception as e:
    print(f"Failed to import posture: {e}")

try:
    from main import draw_skeleton
    print("Successfully imported draw_skeleton")
except Exception as e:
    print(f"Failed to import draw_skeleton: {e}")
