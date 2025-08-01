import cv2
import time
import threading
from logger_config import logger  


def create_capture(rtsp_url):
    cap = cv2.VideoCapture(f"{rtsp_url}?transport=tcp&buffer_size=65536", cv2.CAP_FFMPEG)
    if cap.isOpened():
        cap.set(cv2.CAP_PROP_FPS, 20)
        logger.info(f"🎥 RTSP capture opened successfully: {rtsp_url}")
    else:
        logger.warning(f"⚠️ Failed to open RTSP stream: {rtsp_url}")
    return cap if cap.isOpened() else None


class FrameGrabber(threading.Thread):
    def __init__(self, name, rtsp_url):
        super().__init__()
        self.name = name
        self.rtsp_url = rtsp_url
        self.cap = create_capture(rtsp_url)
        self.lock = threading.Lock()
        self.frame = None
        self.stopped = threading.Event()
        logger.info(f"[{self.name}] 🟢 FrameGrabber initialized.")

    def run(self):
        logger.info(f"[{self.name}] ▶️ FrameGrabber thread started.")
        while not self.stopped.is_set():
            try:
                if self.cap is None or not self.cap.isOpened():
                    logger.warning(f"[{self.name}] 🔄 Reconnecting stream...")
                    self.cap = create_capture(self.rtsp_url)
                    time.sleep(2)
                    continue

                ret, frame = self.cap.read()
                if not ret or frame is None:
                    logger.warning(f"[{self.name}] ❌ Failed to read frame. Releasing and reconnecting.")
                    self.cap.release()
                    time.sleep(2)
                    self.cap = create_capture(self.rtsp_url)
                    continue

                with self.lock:
                    self.frame = frame

                time.sleep(1 / 3)  # CAPTURE_FPS = 3
            except Exception as e:
                logger.exception(f"[{self.name}] 🚨 Exception in FrameGrabber loop: {e}")
                time.sleep(5)

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.stopped.set()
        if self.cap:
            self.cap.release()
        logger.info(f"[{self.name}] 🔴 FrameGrabber stopped.")
