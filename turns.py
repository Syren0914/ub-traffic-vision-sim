"""
Phase 2b: Measure turn movements (origin leg -> destination leg).

Robust version: instead of requiring two line-crossings under one track ID
(which fragments under occlusion), we assign each track an ORIGIN leg from
where it first appears and a DESTINATION leg from where it last appears,
using leg "zones" around the frame edges. Writes the measured O-D flows as a
SUMO routes file.

Run:  python turns.py zddz_5min.mp4 yolo11n.pt 960
"""
import sys
import cv2
from collections import defaultdict
from ultralytics import YOLO

SOURCE = sys.argv[1] if len(sys.argv) > 1 else "zddz_5min.mp4"
MODEL = sys.argv[2] if len(sys.argv) > 2 else "yolo11n.pt"
IMGSZ = int(sys.argv[3]) if len(sys.argv) > 3 else 960
VEHICLE_CLASSES = [2, 3, 5, 7]
MIN_TRAVEL = 70           # px; ignore tracks that barely move (parked/jitter)

EDGE = {"NORTH": ("N_in", "C_N"), "SOUTH": ("S_in", "C_S"),
        "EAST":  ("E_in", "C_E"), "SW":    ("W_in", "C_W")}


def zone(x, y):
    """Which leg region is this point in? (440x360 frame) None = central/ambiguous."""
    if y <= 130:
        return "NORTH"
    if x >= 345 and 140 <= y <= 250:
        return "EAST"
    if x <= 125 and y >= 230:
        return "SW"
    if y >= 288 and x >= 140:
        return "SOUTH"
    return None


model = YOLO(MODEL)
cap = cv2.VideoCapture(SOURCE)
fps = cap.get(cv2.CAP_PROP_FPS) or 7

first_pos, last_pos = {}, {}
frame_count = 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame_count += 1
    r = model.track(frame, persist=True, classes=VEHICLE_CLASSES,
                    tracker="custom_tracker.yaml", imgsz=IMGSZ, verbose=False)
    b = r[0].boxes
    if b is None or b.id is None:
        continue
    for tid, (cx, cy, _, _) in zip(b.id.int().tolist(), b.xywh.tolist()):
        if tid not in first_pos:
            first_pos[tid] = (cx, cy)
        last_pos[tid] = (cx, cy)
    if frame_count % 200 == 0:
        print(f"frame {frame_count}...")

matrix = defaultdict(int)
usable = skip_short = skip_zone = 0
for tid in first_pos:
    fx, fy = first_pos[tid]
    lx, ly = last_pos[tid]
    if (lx-fx)**2 + (ly-fy)**2 < MIN_TRAVEL**2:
        skip_short += 1
        continue
    o, d = zone(fx, fy), zone(lx, ly)
    if o and d and o != d:
        matrix[(o, d)] += 1
        usable += 1
    else:
        skip_zone += 1

video_seconds = frame_count / fps
legs = ["NORTH", "EAST", "SOUTH", "SW"]
print(f"\n{frame_count} frames = {video_seconds:.0f}s | tracks={len(first_pos)} "
      f"usable={usable} skip_short={skip_short} skip_zone={skip_zone}\n")
print("O-D matrix (counts) rows=origin, cols=dest")
print(f"{'':6}" + "".join(f"{d:>7}" for d in legs) + "   inflow")
for o in legs:
    row = "".join(f"{matrix[(o,d)]:>7}" for d in legs)
    inflow = sum(matrix[(o, d)] for d in legs)
    print(f"{o:6}{row}   {inflow}  ({inflow/video_seconds*3600:.0f}/h)")

with open("sumo/zddz_measured.rou.xml", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<!-- MEASURED O-D flows from turns.py (zone endpoints). -->\n')
    f.write('<routes>\n    <vType id="car" vClass="passenger" maxSpeed="13.9"/>\n')
    for o in legs:
        for d in legs:
            c = matrix[(o, d)]
            if c == 0 or o == d:
                continue
            vph = c / video_seconds * 3600
            f.write(f'    <flow id="{o}_{d}" type="car" begin="0" end="600" '
                    f'vehsPerHour="{vph:.0f}" departLane="free">'
                    f'<route edges="{EDGE[o][0]} {EDGE[d][1]}"/></flow>\n')
    f.write('</routes>\n')
print("\nwrote sumo/zddz_measured.rou.xml")
