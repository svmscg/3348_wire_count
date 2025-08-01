import cv2
import os
import requests
import json
from glob import glob
from datetime import datetime
from dotenv import load_dotenv

# ───── Load environment variables ─────
ENV_PATH = r"C:\Users\6078\Desktop\3348_wire_count\.env"
load_dotenv(dotenv_path=ENV_PATH)

# ───── Load configuration from JSON ─────
CONFIG_PATH1 = r"C:\Users\6078\Desktop\3348_wire_count\Telegram_summary\config.json"
with open(CONFIG_PATH1, 'r') as f:
    config = json.load(f)

# ───── CONFIGURATION ─────
LCG_URL = config.get("LCG_CAMERA_URL", "")
PWLC_URL = config.get("PWLC_CAMERA_URL", "")
SNAPSHOT_DIR = r"C:\Users\6078\Desktop\3348_wire_count\Telegram_summary\snapshots_wire"
TELEGRAM_TOKEN1 = config.get("TELEGRAM_TOKEN1", "")
TELEGRAM_CHAT_IDS1 = config.get("TELEGRAM_CHAT_IDS1", [])

os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# ───── SNAPSHOT FUNCTION FOR ANY CAMERA ─────
def capture_snapshot(stream_name, rtsp_url):
    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        print(f"[✗] Unable to open stream for {stream_name}")
        return None

    for _ in range(10):
        cap.read()

    ret, frame = cap.read()
    cap.release()

    if ret:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"{SNAPSHOT_DIR}/{stream_name}_snap_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        print(f"[✓] Snapshot saved: {filename}")
        return filename
    else:
        print(f"[✗] Failed to decode {stream_name} stream")
        return None

# ───── TELEGRAM SEND FUNCTION ─────
def send_snapshots_to_telegram(filepaths):
    for f in filepaths:
        if not f or not os.path.exists(f):
            continue

        with open(f, 'rb') as photo:
            for chat_id in TELEGRAM_CHAT_IDS1:
                response = requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN1}/sendPhoto",
                    data={'chat_id': chat_id},
                    files={'photo': photo}
                )
                print(f"Sent {f} to {chat_id} → {response.status_code}")
                print("Response:", response.json())

        os.remove(f)

# ───── MAIN ─────
if __name__ == "__main__":
    print("📸 Capturing LCG & PWLC snapshots...")
    lcg_file = capture_snapshot("lcg", LCG_URL)
    pwlc_file = capture_snapshot("pwlc", PWLC_URL)

    print("📤 Sending snapshots to Telegram...")
    send_snapshots_to_telegram([lcg_file, pwlc_file])
