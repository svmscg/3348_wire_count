import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import requests
from dotenv import load_dotenv
import statistics

# === Load .env safely for Task Scheduler ===
ENV_PATH = r"C:\Users\6078\Desktop\3348_wire_count\.env"
load_dotenv(dotenv_path=ENV_PATH)

# === Database and Telegram Config ===
db_config = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

CONFIG_PATH1 = r"C:\Users\6078\Desktop\3348_wire_count\Telegram_summary\config.json"
with open(CONFIG_PATH1, 'r') as f:
    config = json.load(f)

# 🔐 Hardcoded Telegram Bot Token and Chat ID
TELEGRAM_TOKEN1 = config.get("TELEGRAM_TOKEN1", "")
TELEGRAM_CHAT_IDS1 = config.get("TELEGRAM_CHAT_IDS1", [])


# === Log file path ===
LOG_PATH = r"C:\Users\6078\Desktop\3348_wire_count\logs\telegram.log"

# === Logging function (safe for emojis) ===
def log(message):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

# === Fetch data between previous 30-minute window ===
def fetch_data_between_half_hour():
    now = datetime.now()
    end_time = now
    start_time = end_time - timedelta(minutes=30)

    query = f"""
    SELECT timestamp, lcg_wire_count, pwlc_wire_count, total_wire_count
    FROM "3348_wire_count"
    WHERE timestamp >= '{start_time}' AND timestamp < '{end_time}'
    ORDER BY timestamp ASC;
"""

    try:
        with psycopg2.connect(**db_config) as conn:
            df = pd.read_sql(query, conn)
            return df
    except Exception as e:
        log(f"❌ DB Error: {e}")
        return pd.DataFrame(columns=["timestamp", "lcg_wire_count", "pwlc_wire_count", "total_wire_count"])

# === Send Telegram alert ===
def send_telegram_alert(msg):
    success_ids = []
    for chat_id in TELEGRAM_CHAT_IDS1:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN1}/sendMessage"
            response = requests.post(url, data={"chat_id": chat_id, "text": msg})
            if response.status_code == 200:
                success_ids.append(str(chat_id))
            else:
                log(f"⚠️ Failed for {chat_id}: {response.text}")
        except Exception as e:
            log(f"❌ Telegram Error for {chat_id}: {e}")

    if success_ids:
        log(f"✅ Telegram message sent to {', '.join(success_ids)}:\n{msg}")
    else:
        log("❌ No Telegram messages sent.")

def hourly_summary():
    now = datetime.now()
    df = fetch_data_between_half_hour()

    # LCG LOGIC
    if 'lcg_wire_count' not in df.columns or df['lcg_wire_count'].dropna().empty:
        lcg_mode = "NA"
    else:
        lcg_data = df['lcg_wire_count'].dropna()
        if (lcg_data == 0).all():
            lcg_mode = 0
        else:
            try:
                lcg_mode = statistics.mode(lcg_data)
            except statistics.StatisticsError:
                lcg_mode = statistics.median(lcg_data)

    # PWLC LOGIC
    if 'pwlc_wire_count' not in df.columns or df['pwlc_wire_count'].dropna().empty:
        pwlc_mode = "NA"
    else:
        pwlc_data = df['pwlc_wire_count'].dropna()
        if (pwlc_data == 0).all():
            pwlc_mode = 0
        else:
            try:
                pwlc_mode = statistics.mode(pwlc_data)
            except statistics.StatisticsError:
                pwlc_mode = statistics.median(pwlc_data)

    # TOTAL LOGIC
   # TOTAL LOGIC – based on LCG + PWLC, capped at 48
    if isinstance(lcg_mode, (int, float)) and isinstance(pwlc_mode, (int, float)):
        total_mode = int(lcg_mode) + int(pwlc_mode)
    else:
         total_mode = "NA"


    # Prepare message
    msg = (
        f"📊 Hourly Wire Count Summary\n"
        f"🕒 Time: {now.strftime('%I:%M %p')}\n"
        f"🔵 LCG Wire: {lcg_mode}\n"
        f"🟢 PWLC Wire: {pwlc_mode}\n"
        f"🟣 Total Wire: {total_mode}\n"
    )

    send_telegram_alert(msg)
    print("✅ Summary sent.")



# === Main trigger ===
if __name__ == "__main__":
    hourly_summary()
    print("✅ Hourly summary executed successfully.")