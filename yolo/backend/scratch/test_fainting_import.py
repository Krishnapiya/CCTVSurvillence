import sys
import os

fainting_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../fainting"))
print("Fainting dir:", fainting_dir)
if fainting_dir not in sys.path:
    sys.path.append(fainting_dir)

try:
    from tracker import PersonTracker
    from posture import analyze_posture, PostureState
    from state_machine import FallStateMachine
    print("Success importing fainting modules!")
except Exception as e:
    print("Failed to import:", e)
