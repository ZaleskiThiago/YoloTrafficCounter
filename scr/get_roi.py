import cv2
import yaml
import os


# 1. Load the configuration to get the video path
def load_video_path(config_file="config.yaml"):
    if not os.path.exists(config_file):
        # Fallback if the file doesn't exist yet
        raise FileNotFoundError(f"{config_file} not found!")

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    return config.get("video_source")


video_path = load_video_path()
cap = cv2.VideoCapture(video_path)
ret, frame = cap.read()
cap.release()

if not ret:
    print(f"Error: Could not read the video file at {video_path}")
    exit()

points = []


def click_event(event, x, y, flags, params):
    global frame
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append([x, y])
        cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
        if len(points) > 1:
            cv2.line(frame, tuple(points[-2]), tuple(points[-1]), (0, 255, 0), 2)

        title = "ROI Selector - Click 4 points. Press 'q' to finish."
        cv2.imshow(title, frame)

        if len(points) == 4:
            cv2.line(frame, tuple(points[-1]), tuple(points[0]), (0, 255, 0), 2)
            cv2.imshow(title, frame)

            print("\n ROI Defined! Copy this into your config.yaml:\n")
            print("roi_points:")
            for pt in points:
                print(f"  - [{pt[0]}, {pt[1]}]")
            print("")


title = "ROI Selector - Click 4 points. Press  lower 'q' to finish."
cv2.imshow(title, frame)
cv2.setMouseCallback(title, click_event)

cv2.waitKey(0)
cv2.destroyAllWindows()
