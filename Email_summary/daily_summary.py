import os
import time
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from PIL import Image
import base64
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication  # <-- Required for attachments
from apscheduler.schedulers.background import BackgroundScheduler
from shift_graph import generate_shift_wire_count_graph

# ─── Load ENV and DB ─────────────────────────────
dotenv_path = os.path.join(r"C:\Users\6078\Desktop\3348_wire_count\.env") # Change path as needed
load_dotenv(dotenv_path)

# Get variables from environment or a config file
DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = os.getenv("DB_PORT", "")
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

encoded_password = quote_plus(DB_PASSWORD)
DB_URL = f"postgresql+psycopg2://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(DB_URL)
    engine.connect() # Attempt to connect to check if the URL is valid
    print("✅ Database connection successful.")
except Exception as e:
    print(f"❌ Failed to connect to the database. Error: {e}")
    # You might want to exit the program here if the DB connection is critical.
    # import sys
    # sys.exit(1)

# ─── Setup Logging ─────────────────────────
logging.basicConfig(
    filename=r"C:\Users\6078\Desktop\3348_wire_count\logs\Email_summary.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)

# ─── Shift Info ─────────────────────────
SHIFTS = {
    "Shift A": (7, 15),
    "Shift B": (15, 23),
    "Shift C": (23, 7)
}

SHIFT_MAIL_TIMES = {
    "Shift A": (15, 0),
    "Shift B": (23, 0),
    "Shift C": (7, 0)
}

# ─── Core Functions ─────────────────────

def get_current_shift_info():
    now = datetime.now()
    for name, (start_hr, end_hr) in SHIFTS.items():
        if start_hr < end_hr:
            if start_hr <= now.hour < end_hr:
                return name, start_hr, end_hr
        else:
            if now.hour >= start_hr or now.hour < end_hr:
                return name, start_hr, end_hr
    return None, None, None

def fetch_shift_hourly_summary(start_hour, end_hour):
    now = datetime.now() - timedelta(minutes=1)
    if start_hour > end_hour:
        start_time = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        if now.hour < end_hour:
            start_time -= timedelta(days=1)
        end_time = start_time + timedelta(hours=(24 - start_hour + end_hour))
    else:
        start_time = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=end_hour - start_hour)

    query = f"""
        SELECT mcid, lcg_wire_count, pwlc_wire_count, total_wire_count, rtms, timestamp
        FROM "3348_wire_count"
        WHERE timestamp >= '{start_time}' AND timestamp < '{end_time}'
        ORDER BY timestamp ASC
    """
    df = pd.read_sql(query, engine)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    summary = []
    for h in range((end_time - start_time).seconds // 3600):
        point = start_time + timedelta(hours=h + 1)
        window_start = point - timedelta(minutes=30)
        hour_df = df[(df['timestamp'] >= window_start) & (df['timestamp'] <= point)]

        if not hour_df.empty:
            summary.append({
                'MCID': hour_df['mcid'].mode().iloc[0] if not hour_df['mcid'].mode().empty else 0,
                'LCG Count': hour_df['lcg_wire_count'].mode().iloc[0] if not hour_df['lcg_wire_count'].mode().empty else 0,
                'PWLC Count': hour_df['pwlc_wire_count'].mode().iloc[0] if not hour_df['pwlc_wire_count'].mode().empty else 0,
                'TOTAL Count': hour_df['total_wire_count'].mode().iloc[0] if not hour_df['total_wire_count'].mode().empty else 0,
                'RTMS Count': hour_df['rtms'].mode().iloc[0] if not hour_df['rtms'].mode().empty else 0,
                'Time': point.strftime('%I:%M %p')
            })
        else:
            summary.append({
                'MCID': 3348,
                'LCG Count': 0,
                'PWLC Count': 0,
                'TOTAL Count': 0,
                'RTMS Count': 0,
                'Time': point.strftime('%I:%M %p')
            })

    return pd.DataFrame(summary), start_time.date(), start_time.strftime('%I:%M %p'), end_time.strftime('%I:%M %p')

def get_base64_image(path):
    with open(path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
    return f"data:image/png;base64,{encoded}"

def render_email_html(data, shift_name, shift_time_str, date_str, graph_base64):
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env = Environment(loader=FileSystemLoader(script_dir))
        template = env.get_template("email.html")
        css_path = os.path.join(script_dir, "email.css")
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        return template.render(
            data=data.to_dict(orient="records"),
            css=css,
            shift_name=shift_name,
            shift_time=shift_time_str,
            graph_base64=graph_base64
        )
    except Exception as e:
        logging.error(f"❌ Error rendering HTML: {e}", exc_info=True)
        raise

def send_email(email_html, shift_name, graph_path):
    try:
        from_addr = os.getenv("EMAIL_SENDER")
        recipients = [email.strip() for email in os.getenv("EMAIL_RECIPIENTS", "").split(",")]
        password = os.getenv("EMAIL_PASSWORD")

        msg = MIMEMultipart("related")
        msg['Subject'] = f"{shift_name} - Furnace-3348 Wire Count Summary"
        msg['From'] = from_addr
        msg['To'] = ", ".join(recipients)

        # Alternative part for HTML body
        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)

        msg_alternative.attach(MIMEText(email_html, "html"))

        # Attach the graph image
        with open(graph_path, 'rb') as f:
            image = MIMEApplication(f.read(), Name=os.path.basename(graph_path))
            image.add_header('Content-ID', '<graph1>')
            image.add_header('Content-Disposition', 'inline', filename=os.path.basename(graph_path))
            msg.attach(image)

        logging.info("📧 Sending email via Gmail SMTP...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_addr, password)
            server.sendmail(from_addr, recipients, msg.as_string())
        logging.info(f"✅ Email sent to: {', '.join(recipients)}")
        print(f"✅ Email sent: {shift_name}")
    except Exception as e:
        logging.error(f"❌ Failed to send email: {e}", exc_info=True)
        raise

def send_shift_report(shift_name):
    try:
        logging.info(f"📩 Generating report for {shift_name}")

        today = datetime.now().date()
        graph_dir = r"C:\Users\6078\Desktop\3348_wire_count\Email_summary\output_graphs"

        if os.path.exists(graph_dir):
            for fname in os.listdir(graph_dir):
                fpath = os.path.join(graph_dir, fname)
                if os.path.isfile(fpath):
                    ftime = datetime.fromtimestamp(os.path.getmtime(fpath)).date()
                    if ftime < today and shift_name.replace(' ', '_') in fname:
                        os.remove(fpath)
                        logging.info(f"🗑️ Deleted old graph: {fpath}")

        start_hr, end_hr = SHIFTS[shift_name]
        df_summary, date_str, shift_start_str, shift_end_str = fetch_shift_hourly_summary(start_hr, end_hr)
        shift_time_str = f"{shift_name} – {shift_start_str} to {shift_end_str}"
        logging.info("🖼️ Preparing graph...")
        graph_path = generate_shift_wire_count_graph(df_summary.copy(), shift_name)
        logging.info(f"✅ Graph saved at: {graph_path}")
        graph_base64 = get_base64_image(graph_path)
        email_html = render_email_html(df_summary, shift_name, shift_time_str, date_str, graph_base64)
        send_email(email_html, shift_name, graph_path)

    except Exception as e:
        logging.error(f"❌ Error in shift report for {shift_name}: {e}", exc_info=True)

# ─── Schedule Shifts 1 Min Before End ─────────────

def schedule_all_shifts():
    scheduler = BackgroundScheduler()
    for shift, (mail_hr, mail_min) in SHIFT_MAIL_TIMES.items():
        minute = mail_min - 1 if mail_min > 0 else 59
        hour = mail_hr if mail_min > 0 else (mail_hr - 1) % 24
        scheduler.add_job(
            send_shift_report,
            'cron',
            args=[shift],
            hour=hour,
            minute=minute,
            id=f"{shift}_job"
        )
        logging.info(f"🕒 Scheduled {shift} email at {hour:02}:{minute:02}")
    scheduler.start()
    print("✅ All shifts scheduled successfully.")
    return scheduler

# ─── Main Start ─────────────────────────
if __name__ == "__main__":
    logging.info("🚀 Starting daily summary scheduler...")

    shift_name, start_hr, end_hr = get_current_shift_info()
    if shift_name:
        send_shift_report(shift_name)
    else:
        logging.warning("⚠️ No current shift detected.")

    scheduler = schedule_all_shifts()

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logging.warning("🛑 Scheduler stopped.")
        scheduler.shutdown()


