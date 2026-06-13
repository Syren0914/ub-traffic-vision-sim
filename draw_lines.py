"""
Overlay a coordinate grid + proposed counting lines on the clean frame,
so we can agree on where to count before writing the counter.
Edit LINES below (pixel coords in a 440x360 image) and rerun.
"""
import cv2

frame = cv2.imread("first_frame.jpg")
h, w = frame.shape[:2]

# Proposed counting lines: name -> ((x1,y1),(x2,y2), color BGR)
LINES = {
    "SOUTH (toward camera)": ((150, 235), (320, 235), (0, 0, 255)),
    "WEST":                  ((70, 135),  (70, 188),  (255, 0, 0)),
    "EAST":                  ((395, 180), (395, 228), (0, 200, 0)),
    "NW (the jam)":          ((95, 118),  (190, 138), (0, 165, 255)),
}

# faint grid every 40px with labels, so you can give me exact coords
for x in range(0, w, 40):
    cv2.line(frame, (x, 0), (x, h), (90, 90, 90), 1)
    cv2.putText(frame, str(x), (x + 1, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (200, 200, 200), 1)
for y in range(0, h, 40):
    cv2.line(frame, (0, y), (w, y), (90, 90, 90), 1)
    cv2.putText(frame, str(y), (1, y + 11), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (200, 200, 200), 1)

for name, (p1, p2, color) in LINES.items():
    cv2.line(frame, p1, p2, color, 3)
    cv2.putText(frame, name, (p1[0], p1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

cv2.imwrite("lines_preview.jpg", frame)
print("wrote lines_preview.jpg")
