import sys
import os

# Ensure the app parent directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def run_tests():
    print("==================================================")
    print("AI Surveillance Platform Backend Verification")
    print("==================================================")
    
    modules_to_test = [
        "app.core.config",
        "app.core.database",
        "app.core.security",
        "app.models.user",
        "app.models.camera",
        "app.models.event",
        "app.models.alert",
        "app.models.verification",
        "app.models.audit",
        "app.models",
        "app.repositories.base",
        "app.repositories.user",
        "app.repositories.camera",
        "app.repositories.event",
        "app.repositories.alert",
        "app.services.websocket_manager",
        "app.services.ai_verification",
        "app.services.video_manager",
        "app.services.ai_engine",
        "app.services.camera_manager",
        "app.services.stream_processor",
        "app.services.event_engine",
        "app.services.alert_manager",
        "app.workers.celery_app",
        "app.workers.tasks",
        "app.main"
    ]

    all_passed = True

    for mod in modules_to_test:
        try:
            print(f"Testing import of {mod}... ", end="")
            # We temporarily override stdout/stderr or catch errors to print clean output
            __import__(mod)
            print("✅ PASSED")
        except Exception as e:
            print(f"❌ FAILED\nReason: {e}")
            all_passed = False

    print("==================================================")
    if all_passed:
        print("🎉 Verification complete. All modules imported successfully with no syntax or circular dependency issues!")
        sys.exit(0)
    else:
        print("⚠️ Verification failed. Some modules could not be imported.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
