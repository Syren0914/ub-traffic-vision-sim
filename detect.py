"""
Phase 1a: Detect + track vehicles on the live Ulaanbaatar traffic stream.

What this does:
  1. Opens the live HLS stream with OpenCV (ffmpeg backend).
  2. Runs a PRETRAINED YOLO model (no training needed) on each frame.
  3. Keeps a stable ID on each vehicle across frames (ByteTrack).
  4. Draws boxes + IDs and writes an annotated .mp4 we can watch.
  5. Saves one clean frame (first frame) so we can plan counting lines.

Run:  python detect.py
Stop early: Ctrl+C  (it will still save what it captured so far)
"""

import sys
import time
import cv2
from ultralytics import YOLO

# ----- settings you can tweak -----
# Pass a video file or an HLS URL you have the rights to use.
SOURCE = sys.argv[1] if len(sys.argv) > 1 else "your_clip.mp4"
DURATION_SECONDS = 20          # how long to capture
OUTPUT_VIDEO = "annotated.mp4"
FIRST_FRAME = "first_frame.jpg"

# COCO class IDs for vehicles: 2=car, 3=motorcycle, 5=bus, 7=truck
VEHICLE_CLASSES = [2, 3, 5, 7]
# ----------------------------------

# "yol11n" = nano = smallest/fastest. Auto-downloads the first time (~5 MB).
model = YOLO("yolo11n.pt")

cap = cv2.VideoCapture(SOURCE)
if not cap.isOpened():
    raise SystemExit(f"Could not open source: {SOURCE}")

# Figure out the stream's size + fps so our output video matches.
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
if fps <= 0 or fps > 60:
    fps = 25  # streams sometimes report garbage; 25 is a safe default
print(f"Stream opened: {width}x{height} @ {fps:.0f} fps")

writer = cv2.VideoWriter(
    OUTPUT_VIDEO, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
)

seen_ids = set()      # every unique vehicle ID we've ever seen
start = time.time()
frame_count = 0

try:
    while time.time() - start < DURATION_SECONDS:
        ok, frame = cap.read()
        if not ok:
            print("Frame read failed (stream hiccup), retrying...")
            continue

        frame_count += 1
        if frame_count == 1:
            cv2.imwrite(FIRST_FRAME, frame)  # save a clean frame for planning

        # track() = detect + assign IDs. persist=True keeps IDs across calls.
        results = model.track(
            frame, persist=True, classes=VEHICLE_CLASSES,
            tracker="bytetrack.yaml", verbose=False
        )

        # Count how many vehicles are visible right now + collect their IDs.
        boxes = results[0].boxes
        current = 0
        if boxes is not None and boxes.id is not None:
            current = len(boxes.id)
            for tid in boxes.id.int().tolist():
                seen_ids.add(tid)

        # results[0].plot() gives us a frame with boxes/IDs drawn on it.
        annotated = results[0].plot()
        cv2.putText(
            annotated, f"On screen: {current}   Total unique: {len(seen_ids)}",
            (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
        )
        writer.write(annotated)

        if frame_count % 10 == 0:
            print(f"frame {frame_count}: {current} on screen, "
                  f"{len(seen_ids)} unique so far")

except KeyboardInterrupt:
    print("\nStopped early by user.")

finally:
    cap.release()
    writer.release()
    print(f"\nDone. Processed {frame_count} frames.")
    print(f"Total unique vehicles seen: {len(seen_ids)}")
    print(f"Annotated video -> {OUTPUT_VIDEO}")
    print(f"Clean frame     -> {FIRST_FRAME}")
