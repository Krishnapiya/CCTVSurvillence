import cv2
from ultralytics import YOLO

# -----------------------------------
# LOAD MODELS
# -----------------------------------

human_model = YOLO("yolov8s.pt")

fire_model = YOLO(
    "/media/ai/1646F35346F3325B/yolo_survialance/runs/detect/train/weights/best.pt"
)

# -----------------------------------
# LOAD IMAGE
# -----------------------------------

image_path = "/home/ai/Desktop/mfs1.jpeg"

frame = cv2.imread(image_path)

# -----------------------------------
# HUMAN + MOBILE DETECTION
# -----------------------------------

results = human_model(frame)

for r in results:

    for box in r.boxes:

        cls = int(box.cls[0])
        label = human_model.names[cls]

        conf = float(box.conf[0])

        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0]
        )

        # PERSON
        if label == "person":

            color = (0, 255, 0)

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

            cv2.putText(
                frame,
                f"Person {conf:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

        # MOBILE
        elif label == "cell phone":

            color = (255, 0, 0)

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

            cv2.putText(
                frame,
                f"Mobile {conf:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

# -----------------------------------
# FIRE / SMOKE DETECTION
# -----------------------------------

fire_results = fire_model(frame)

for r in fire_results:

    for box in r.boxes:

        cls = int(box.cls[0])
        label = fire_model.names[cls]

        conf = float(box.conf[0])

        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0]
        )

        if label == "fire":
            color = (0, 0, 255)

        else:
            color = (180, 180, 180)

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        cv2.putText(
            frame,
            f"{label} {conf:.2f}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )
# -----------------------------------
# SAVE RESULT
# -----------------------------------

import os

save_dir = "/media/ai/1646F35346F3325B/yolo_survialance/runs/detect/custom_predict"

# Create folder automatically
os.makedirs(
    save_dir,
    exist_ok=True
)

output_path = os.path.join(
    save_dir,
    "output.jpg"
)

# Save detected image
cv2.imwrite(
    output_path,
    frame
)

print(f"\nOutput saved to: {output_path}")

# -----------------------------------
# OPTIONAL DISPLAY
# -----------------------------------

# Uncomment below only if OpenCV GUI works

# cv2.imshow(
#     "AI Surveillance Detection",
#     frame
# )

# cv2.waitKey(0)
# cv2.destroyAllWindows()
