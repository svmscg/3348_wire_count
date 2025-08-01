import threading
from ultralytics import YOLO
from dotenv import load_dotenv
import os
from frame_grabber import FrameGrabber
from detector import run_detection
from display import display_frames
from database_handle import db_handler
from database_handle.db_handler import insert_to_db
from logger_config import logger

# Load environment variables
load_dotenv()

MCID = int(os.getenv("MCID", 0))
MODEL_PATH = os.getenv("MODEL_PATH")
CAMERA_LCG = os.getenv("LCG_CAMERA_URL","")
CAMERA_PWLC = os.getenv("PWLC_CAMERA_URL","")


def main():
    logger.info("🚀 Starting Wire Count System")

    try:
        model = YOLO(MODEL_PATH)
        logger.info(f"✅ YOLO model loaded: {MODEL_PATH}")
    except Exception as e:
        logger.exception("❌ Failed to load YOLO model")
        return

    # ✅ Pass name + rtsp_url
    grabber_lcg = FrameGrabber("LCG", CAMERA_LCG)
    grabber_pwlc = FrameGrabber("PWLC", CAMERA_PWLC)
    grabber_lcg.start()
    grabber_pwlc.start()

    results = {"LCG": {}, "PWLC": {}}
    lock = threading.Lock()

    threads = [
        threading.Thread(target=run_detection, args=(grabber_lcg, model, results, lock, "LCG")),
        threading.Thread(target=run_detection, args=(grabber_pwlc, model, results, lock, "PWLC")),
        threading.Thread(target=insert_to_db, args=(results, lock, MCID)),
    ]

    for t in threads:
        t.start()

    try:
        display_frames(results, lock)
    except Exception as e:
        logger.exception("❌ Display error")
    finally:
        grabber_lcg.stop()
        grabber_pwlc.stop()
        for t in threads:
            t.join()
        logger.info("🛑 Wire Count System shut down cleanly.")

if __name__ == "__main__":
    main()
