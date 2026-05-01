import warnings
import sys

# ==========================================
# DEPENDENCIES CHECK (WOULD THE STD OPTION BE BETTER? MAYBE, SAFETY MEASURES ONLY)
# ==========================================
DEPENDENCIES = {
    "cv2": "opencv-python",
    "numpy": "numpy",
    "ultralytics": "ultralytics",
    "openpyxl": "openpyxl",
    "yaml": "pyyaml",
}


def check_dependencies():
    missing = []
    for module_name, pip_name in DEPENDENCIES.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        install_cmd = f"pip install {' '.join(missing)}"
        warnings.warn(
            f"\n\n[!] MISSING DEPENDENCIES DETECTED\n"
            f"The traffic counter requires: {', '.join(missing)}\n"
            f"Please run the following command to fix your environment:\n\n"
            f"    {install_cmd}\n",
            ImportWarning,
        )
        sys.exit(1)


check_dependencies()

# ==========================================
# iMPORTS AFTER CHECKING
# ==========================================
import yaml
import cv2
import numpy as np
from datetime import datetime
from ultralytics import YOLO
import os
from openpyxl import Workbook


def load_config(file_path="config.yaml"):
    if not os.path.exists(file_path):
        # Fallback if the file doesn't exist yet
        raise FileNotFoundError(f"{file_path} not found!")

    with open(file_path, "r") as f:
        config = yaml.safe_load(f)

    # Convert ROI points back to the numpy format OpenCV needs
    config["roi_points"] = np.array(config["roi_points"], dtype=np.int32)
    return config


# ==========================================
# CONFIGURATION SETTINGS
# ==========================================
CONFIG = load_config()
LINE_DIRECTION = CONFIG["line_direction"]
LINE_POSITION = CONFIG["line_position"]
OFFSET = CONFIG["offset"]  # Tolerance zone for counting
ROI_POINTS = CONFIG["roi_points"]
VIDEO_SOURCE = CONFIG["video_source"]
YOLO_MODEL = CONFIG["model_path"]
OUTPUT_VIDEO = CONFIG["output_video_name"]
OUTPUT_EXCEL = CONFIG["output_excel_name"]


def main():
    # ==========================================
    # VALIDATE ROI POINTS ARE PROPERLY LOADED
    # ==========================================
    if not isinstance(ROI_POINTS, np.ndarray):
        raise TypeError(
            """Dev, you didn't setup ROI_POINTS \n 
            Make sure to run get_roi.py first to get the roi region and paste it on config.yaml"""
        )

    # ==========================================
    # CREATING CROPS FOLDER
    # ==========================================
    if CONFIG["save_crops"]:
        os.makedirs("crops", exist_ok=True)

    # ==========================================
    # LOADING YOLO & VIDEO SOURCE
    # ==========================================
    model = YOLO(YOLO_MODEL)
    cap = cv2.VideoCapture(VIDEO_SOURCE)

    # ==========================================
    # COMMOM VIDEO INFO
    # ==========================================
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    print(f"{frame_width}x{frame_height} - {fps}FPS")

    # ==========================================
    # VIDEO OUTPUT CONFIG
    # ==========================================
    # @TODO OUTPUT VIDEO SWITCH FROM YAML
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, fps, (frame_width, frame_height))

    counted_ids = set()
    vehicle_counts = {"car": 0, "truck": 0, "motorcycle": 0}
    TARGET_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck

    # ==========================================
    # EXCEL CONFIGURATION (CSV WOULD BE FINE, BUT THE SAVE_CROP FEATURE MAKES BETTER FOR REPORTS/VALIDATION TRUST ME)
    # ==========================================
    wb = Workbook()
    ws = wb.active
    ws.title = "Traffic Log"
    if CONFIG["save_crops"]:
        ws.append(["Timestamp", "Vehicle Type", "Tracking ID", "Photo Link"])
    else:
        ws.append(["Timestamp", "Vehicle Type", "Tracking ID"])

    excel_filename = OUTPUT_EXCEL

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # ==========================================
        # TRACKING CONFIGURATION
        # ==========================================
        results = model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            imgsz=736,
            classes=TARGET_CLASSES,
            verbose=False,
        )

        # ==========================================
        # ROI DRAW ON VIDEO FEED
        # ==========================================
        cv2.polylines(
            frame, [ROI_POINTS], isClosed=True, color=(255, 0, 255), thickness=2
        )

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            class_ids = results[0].boxes.cls.int().cpu().tolist()

            for box, track_id, class_id in zip(boxes, track_ids, class_ids):
                x1, y1, x2, y2 = map(int, box)
                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                class_name = model.names[class_id]

                is_inside_roi = cv2.pointPolygonTest(ROI_POINTS, (cx, cy), False) >= 0

                if is_inside_roi:
                    # ==========================================
                    # VEHICLE BOX DRAW WITH CENTER DOT
                    # ==========================================
                    cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

                    # ==========================================
                    # LINE DIRECTION/ORIENTATION SETUP
                    # ==========================================
                    if LINE_DIRECTION == "horizontal":
                        is_crossing = (
                            (LINE_POSITION - OFFSET) < cy < (LINE_POSITION + OFFSET)
                        )
                    elif LINE_DIRECTION == "vertical":  # vertical
                        is_crossing = (
                            (LINE_POSITION - OFFSET) < cx < (LINE_POSITION + OFFSET)
                        )
                    else:
                        raise ValueError(
                            f"config.yaml -> line_direction value is not an accepted value: '{LINE_DIRECTION}' expected: 'horizontal' or 'vertical'"
                        )

                    # ==========================================
                    # VEHICLE LOG
                    # ==========================================
                    if is_crossing:
                        if track_id not in counted_ids:
                            counted_ids.add(track_id)

                            if class_name == "car":
                                vehicle_counts["car"] += 1
                            elif class_name == "motorcycle":
                                vehicle_counts["motorcycle"] += 1
                            elif class_name in ["truck", "bus"]:
                                vehicle_counts["truck"] += 1
                                class_name = "truck"

                            # FIX FOR ANNOYNG BUG THAT CRASHED IF THE DRAWN BOX WAS GETTING OUTSIDE THE SCREEN
                            h, w = frame.shape[:2]
                            crop_y1, crop_y2 = max(0, y1), min(h, y2)
                            crop_x1, crop_x2 = max(0, x1), min(w, x2)
                            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            if CONFIG["save_crops"]:
                                cropped_car = frame[crop_y1:crop_y2, crop_x1:crop_x2]
                                img_filename = f"crops/{class_name}_ID{track_id}.jpg"

                                if cropped_car.size > 0:
                                    cv2.imwrite(img_filename, cropped_car)

                                # 4. Log directly to Excel

                                excel_link = (
                                    f'=HYPERLINK("{img_filename}", "View Photo")'
                                )
                                ws.append([now, class_name, track_id, excel_link])
                            else:
                                ws.append([now, class_name, track_id])

                    # Display ID and Class Name
                    display_text = f"ID: {track_id} {class_name}"
                    cv2.putText(
                        frame,
                        display_text,
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 0),
                        2,
                    )

        # --- DYNAMIC DRAWING LOGIC ---
        # Draw the counting line based on the direction
        if LINE_DIRECTION == "horizontal":
            cv2.line(
                frame, (0, LINE_POSITION), (frame_width, LINE_POSITION), (0, 0, 255), 3
            )
        else:  # vertical
            cv2.line(
                frame, (LINE_POSITION, 0), (LINE_POSITION, frame_height), (0, 0, 255), 3
            )

        # Display the total counts
        count_text = f"Cars: {vehicle_counts['car']} | Trucks: {vehicle_counts['truck']} | motorcycle: {vehicle_counts['motorcycle']}"
        cv2.putText(
            frame, count_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3
        )

        # Write the frame
        out.write(frame)
        cv2.imshow("Traffic Counter", frame)

        if cv2.waitKey(1) & 0xFF == ord(
            "q"
        ):  # lower-case 'q' uppercase (while Caps Lock would not trigger)
            break

    # Final save and cleanup
    wb.save(excel_filename)
    cap.release()
    out.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
