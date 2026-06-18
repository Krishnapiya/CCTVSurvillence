from ultralytics import YOLO

# Load pretrained YOLOv8 model
model = YOLO("yolov8m.pt")

# Train model
model.train(
    data="/media/ai/1646F35346F3325B/yolo_survialance/Fire And Smoke Detection.v1i.yolov8/data.yaml",

    # Training
    epochs=150,
    patience=25,

    # Image settings
    imgsz=640,
    batch=16,

    # GPU
    device=0,

    # Optimizer
    optimizer="AdamW",
    lr0=0.001,
    weight_decay=0.0005,

    # Augmentation
    augment=True,
    mixup=0.15,
    copy_paste=0.1,

    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.4,

    degrees=10,
    translate=0.1,
    scale=0.5,
    fliplr=0.5,

    # Performance
    cache=True,
    workers=8,

    # Validation
    val=True,

    # Save
    save=True,
    save_period=10,

    # Logging
    plots=True,
    verbose=True
)

print("✅ Training completed")
