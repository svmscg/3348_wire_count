# detector.py

import statistics
from datetime import datetime
import traceback
from utils import is_blurry
from database_handle import db_handler

# ── Stream-specific confidence thresholds ──
CONF_THRESHOLDS = {
    "LCG": 0.55,
    "PWLC": 0.62,
}

CROP_WIDTH_RATIO = 0.85
INSERT_INTERVAL = 60  # seconds

def run_detection(grabber, model, results, lock, name):
    wire_history = []
    last_insert_time = datetime.now()

    while not grabber.stopped.is_set():
        frame = grabber.get_frame()
        if frame is None or is_blurry(frame):
            print("⚠️ Skipped blurry or empty frame")
            continue

        # Crop center region
        crop_width = int(frame.shape[1] * CROP_WIDTH_RATIO)
        crop_x = (frame.shape[1] - crop_width) // 2
        frame = frame[:, crop_x:crop_x + crop_width]

        try:
            result = model(frame)[0]
        except Exception:
            traceback.print_exc()
            continue

        # Use stream-specific threshold
        conf_thresh = CONF_THRESHOLDS.get(name, 0.55)
        wire_count = sum(1 for box in result.boxes if float(box.conf) > conf_thresh)
        now = datetime.now()
        wire_history.append((now, wire_count))
        wire_history = [(ts, wc) for ts, wc in wire_history if (now - ts).total_seconds() <= 60]

        with lock:
            results[name]["frame"] = result.plot()
            results[name]["wire_count"] = wire_count
            results[name]["mode"] = (
                statistics.mode([wc for _, wc in wire_history]) if wire_history else 0
            )

        if (now - last_insert_time).total_seconds() >= INSERT_INTERVAL:
            last_insert_time = now
