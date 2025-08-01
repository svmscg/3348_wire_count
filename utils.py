import cv2
import numpy as np
import subprocess
import requests
from dotenv import load_dotenv
import os
from logger_config import logger  


def is_blurry(frame, threshold=180.0):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F).var()
    is_blur = lap < threshold
    return is_blur


def capture_snapshot_via_ffmpeg(rtsp_url, output_path="frame.jpg"):
    cmd = [
        "ffmpeg", "-rtsp_transport", "tcp", "-loglevel", "quiet", "-y",
        "-i", rtsp_url, "-frames:v", "1", "-q:v", "2", output_path
    ]
    try:
        subprocess.run(cmd, timeout=10, check=True)
        return cv2.imread(output_path)
    except subprocess.TimeoutExpired:
        logger.warning(f"⏰ FFmpeg snapshot timed out for {rtsp_url}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ FFmpeg snapshot failed → {e}")
    except Exception as e:
        logger.exception(f"⚠️ Unexpected error during FFmpeg snapshot: {e}")
    return None


def get_ideal_wire_count():
    
    load_dotenv()
    url = os.getenv("API_LINK_RTMS", "")
    
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        running = [d for d in data if d["acSpeed"] > 1]
        count = len(running)
        logger.info(f"🌐 RTMS API returned {count} running wire")
        return count
    except requests.exceptions.RequestException as e:
        logger.warning(f"🌐 RTMS API request failed: {e}")
    except Exception as e:
        logger.exception("⚠️ Unexpected error in get_ideal_wire_count()")
    return 0

