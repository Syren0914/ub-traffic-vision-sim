"""Quick probe: detections + speed for nano vs medium on a few frames."""
import time
import cv2
from ultralytics import YOLO

VEHICLE_CLASSES = [2, 3, 5, 7]
N = 15
cap = cv2.VideoCapture("zddz_5min.mp4")
# grab frame 200 onward (mid-jam, lots of distant cars)
cap.set(cv2.CAP_PROP_POS_FRAMES, 200)
frames = []
for _ in range(N):
    ok, f = cap.read()
    if ok:
        frames.append(f)
cap.release()

for model_name, imgsz in [("yolo11n.pt", 960), ("yolo11s.pt", 960)]:
    m = YOLO(model_name)
    m.predict(frames[0], classes=VEHICLE_CLASSES, imgsz=imgsz, verbose=False)  # warmup
    t0 = time.time()
    total = 0
    for f in frames:
        r = m.predict(f, classes=VEHICLE_CLASSES, imgsz=imgsz, verbose=False)
        total += len(r[0].boxes)
    dt = time.time() - t0
    per = dt / len(frames)
    eta = per * 2096 / 60
    print(f"{model_name} @ {imgsz}: {total/len(frames):.1f} vehicles/frame avg, "
          f"{per:.2f}s/frame, ETA for 2096 frames ~ {eta:.0f} min")
