"""
Phase 1b: Throughput counter.
Counts vehicles crossing a line on each approach, then converts to vehicles/hour.

Run:  python count.py            (defaults to 60 seconds of capture)
      python count.py 120        (capture longer for a steadier rate)
"""
import sys
import time
import cv2
from ultralytics import YOLO

VEHICLE_CLASSES = [2, 3, 5, 7]          # car, motorcycle, bus, truck
# Args:  python count.py <source> [model] [imgsz]
SOURCE = sys.argv[1] if len(sys.argv) > 1 else "traffic.mp4"
MODEL = sys.argv[2] if len(sys.argv) > 2 else "yolo11n.pt"
IMGSZ = int(sys.argv[3]) if len(sys.argv) > 3 else 640   # inference resolution
IS_FILE = not SOURCE.lower().startswith("http")
OUTPUT_VIDEO = "annotated_count.mp4"

# Counting lines (pixel coords in the 440x360 frame): name -> ((x1,y1),(x2,y2), color)
# Zuun Dorvon Zam (cam 32786) legs, one line per approach (440x360 frame):
LINES = {
    "NORTH": ((100, 103), (258, 103), (255, 0, 0)),    # avenue at the top
    "SW":    ((10, 243),  (105, 298), (0, 200, 0)),    # left corridor, bottom-left
    "SOUTH": ((215, 305), (348, 330), (0, 0, 255)),    # right corridor, bottom
    "EAST":  ((358, 165), (358, 222), (0, 165, 255)),  # cross-road on the right
}


def segments_intersect(p1, p2, p3, p4):
    """True if segment p1-p2 crosses segment p3-p4."""
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])
    d1 = ccw(p3, p4, p1)
    d2 = ccw(p3, p4, p2)
    d3 = ccw(p1, p2, p3)
    d4 = ccw(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


model = YOLO(MODEL)
print(f"model={MODEL}  imgsz={IMGSZ}")
cap = cv2.VideoCapture(SOURCE)
if not cap.isOpened():
    raise SystemExit(f"Could not open source: {SOURCE}")

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
if fps <= 0 or fps > 60:
    fps = 7
writer = cv2.VideoWriter(OUTPUT_VIDEO, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
print(f"Source {SOURCE}  {width}x{height} @ {fps:.0f}fps")

def cross_sign(a, b, prev, cur):
    """Which way did the vehicle cross the line? +1 or -1 (sign of line x motion)."""
    lx, ly = b[0] - a[0], b[1] - a[1]           # line direction
    mx, my = cur[0] - prev[0], cur[1] - prev[1] # motion direction
    return 1 if (lx * my - ly * mx) >= 0 else -1


last_pos = {}                                   # track id -> last centroid
counted = {name: set() for name in LINES}       # line -> set of ids already counted
# each line counts two opposing flows: '+' and '-'
counts = {name: {1: 0, -1: 0} for name in LINES}

frame_count = 0
try:
    while True:
        ok, frame = cap.read()
        if not ok:
            break               # end of file (or stream dropped)
        frame_count += 1

        results = model.track(frame, persist=True, classes=VEHICLE_CLASSES,
                              tracker="bytetrack.yaml", imgsz=IMGSZ, verbose=False)
        boxes = results[0].boxes
        annotated = results[0].plot()

        if boxes is not None and boxes.id is not None:
            ids = boxes.id.int().tolist()
            xywh = boxes.xywh.tolist()           # center x, center y, w, h
            for tid, (cx, cy, _, _) in zip(ids, xywh):
                cur = (cx, cy)
                prev = last_pos.get(tid)
                if prev is not None:
                    for name, (a, b, _c) in LINES.items():
                        if tid in counted[name]:
                            continue
                        if segments_intersect(prev, cur, a, b):
                            counts[name][cross_sign(a, b, prev, cur)] += 1
                            counted[name].add(tid)
                last_pos[tid] = cur

        # draw the counting lines + live tallies (both directions)
        for name, (a, b, color) in LINES.items():
            cv2.line(annotated, a, b, color, 2)
            cv2.putText(annotated, f"{name}: +{counts[name][1]}/-{counts[name][-1]}",
                        (a[0], a[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
        writer.write(annotated)

        if frame_count % 40 == 0:
            print(f"frame {frame_count}: " +
                  ", ".join(f"{n}=+{counts[n][1]}/-{counts[n][-1]}" for n in LINES))

except KeyboardInterrupt:
    print("\nStopped early.")
finally:
    cap.release()
    writer.release()
    video_seconds = frame_count / fps           # real footage time we processed
    print("\n===================== THROUGHPUT =====================")
    print(f"Processed {frame_count} frames = {video_seconds:.1f}s of footage")
    print(f"{'line':<8} {'dir':>4} {'crossed':>7} {'veh/hour':>9}")
    for name in LINES:
        for d in (1, -1):
            n = counts[name][d]
            per_hour = n / video_seconds * 3600 if video_seconds else 0
            print(f"{name:<8} {('+' if d==1 else '-'):>4} {n:>7} {per_hour:>9.0f}")
    print("=====================================================")
    print(f"Annotated video -> {OUTPUT_VIDEO}")
