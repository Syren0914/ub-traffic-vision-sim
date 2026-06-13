"""Draw candidate counting lines over an image (no YOLO) to confirm placement fast.
Keep LINES in sync with count.py."""
import sys
import cv2

LINES = {
    "NORTH": ((100, 103), (258, 103), (255, 0, 0)),
    "SW":    ((10, 243),  (105, 298), (0, 200, 0)),
    "SOUTH": ((215, 305), (348, 330), (0, 0, 255)),
    "EAST":  ((358, 165), (358, 222), (0, 165, 255)),
}

img_path = sys.argv[1] if len(sys.argv) > 1 else "zddz_trails.jpg"
out = sys.argv[2] if len(sys.argv) > 2 else "zddz_lines_preview.jpg"

img = cv2.imread(img_path)
for name, (a, b, color) in LINES.items():
    cv2.line(img, a, b, color, 3)
    cv2.putText(img, name, (a[0], a[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
cv2.imwrite(out, img)
print("wrote", out)
