"""
Diagnostic: draw every tracked vehicle's path over the clip onto one image.
Shows us where traffic ACTUALLY flows, so we can place counting lines correctly,
and reveals whether tracking is stable (long smooth trails) or fragmented.
"""
import os
import sys
import cv2
import numpy as np
from collections import defaultdict
from ultralytics import YOLO

SOURCE = sys.argv[1] if len(sys.argv) > 1 else "traffic.mp4"
OUT = sys.argv[2] if len(sys.argv) > 2 else "trails.jpg"
MAX_FRAMES = int(sys.argv[3]) if len(sys.argv) > 3 else None  # cap for speed
VEHICLE_CLASSES = [2, 3, 5, 7]

model = YOLO("yolo11n.pt")
cap = cv2.VideoCapture(SOURCE)
ok, first = cap.read()
# TRAILS_BLACK=1 draws paths on a black canvas (footage-free, for publishing)
canvas = np.zeros_like(first) if os.environ.get("TRAILS_BLACK") == "1" else first.copy()

paths = defaultdict(list)            # track id -> list of (x,y) centroids
cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # rewind
n = 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    n += 1
    if MAX_FRAMES and n > MAX_FRAMES:
        break
    r = model.track(frame, persist=True, classes=VEHICLE_CLASSES,
                    tracker="bytetrack.yaml", verbose=False)
    b = r[0].boxes
    if b is not None and b.id is not None:
        for tid, (cx, cy, _, _) in zip(b.id.int().tolist(), b.xywh.tolist()):
            paths[tid].append((int(cx), int(cy)))
cap.release()

# Draw each path in a random-ish color; mark start (green) and end (red).
lengths = []
for tid, pts in paths.items():
    lengths.append(len(pts))
    if len(pts) < 2:
        continue
    color = tuple(int(c) for c in np.random.default_rng(tid).integers(60, 255, 3))
    for i in range(1, len(pts)):
        cv2.line(canvas, pts[i - 1], pts[i], color, 1)
    cv2.circle(canvas, pts[0], 3, (0, 255, 0), -1)
    cv2.circle(canvas, pts[-1], 3, (0, 0, 255), -1)

cv2.imwrite(OUT, canvas)
lengths.sort(reverse=True)
print(f"frames={n}  unique tracks={len(paths)}")
print(f"track lengths (frames) top10: {lengths[:10]}")
print(f"tracks lasting >=10 frames: {sum(1 for l in lengths if l >= 10)}")
print(f"wrote {OUT}  (green=start dot, red=end dot)")
