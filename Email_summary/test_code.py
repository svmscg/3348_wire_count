import os
import time
import base64
import logging
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine
from jinja2 import Environment, FileSystemLoader
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from apscheduler.schedulers.background import BackgroundScheduler
from test import generate_24hr_wire_count_graph  # Custom plotting function

# ─── Load ENV and DB ─────────────────────────────
dotenv_path = os.path.join("C:/Users/6078/Desktop/3348_wire_count", ".env")
load_dotenv(dotenv_path)
DB_URL = os.getenv("DB_URL", "")
engine = create_engine(DB_URL)

# ─── Logging ───────────────────────────────
logging.basicConfig(
    filename=r"C:\Users\6078\Desktop\3348_wire_count\logs\summary.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)

# ─── Fetch Data for 7AM to 7AM Range ───────────────────────────────
def fetch_7am_to_7am_summary():
    now = datetime.now()
    end_time = now.replace(hour=7, minute=0, second=0, microsecond=0)
    if now.hour < 7:
        end_time -= timedelta(days=1)
    start_time = end_time - timedelta(days=1)

    query = f"""
        SELECT mcid, lcg_wire_count, pwlc_wire_count, total_wire_count, rtms, timestamp
        FROM 3348_wire_count
        WHERE timestamp >= '{start_time}' AND timestamp < '{end_time}'
        ORDER BY timestamp ASC
    """
    df = pd.read_sql(query, engine)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    summary = []
    for h in range(24):
        point = start_time + timedelta(hours=h + 1)
        window_start = point - timedelta(minutes=30)
        hour_df = df[(df['timestamp'] >= window_start) & (df['timestamp'] <= point)]

        summary.append({
            'MCID': hour_df['mcid'].mode().iloc[0] if not hour_df['mcid'].mode().empty else 0,
            'LCG Count': hour_df['lcg_wire_count'].mode().iloc[0] if not hour_df['lcg_wire_count'].mode().empty else 0,
            'PWLC Count': hour_df['pwlc_wire_count'].mode().iloc[0] if not hour_df['pwlc_wire_count'].mode().empty else 0,
            'TOTAL Count': hour_df['total_wire_count'].mode().iloc[0] if not hour_df['total_wire_count'].mode().empty else 0,
            'RTMS Count': hour_df['rtms'].mode().iloc[0] if not hour_df['rtms'].mode().empty else 0,
            'Time': point.strftime('%I:%M %p')
        })

    return pd.DataFrame(summary), start_time.date()

def get_base64_image(path):
    with open(path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
    return f"data:image/png;base64,{encoded}"

def render_email_html(data, date_str, graph_base64):
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
            shift_name="3348 Wire Count (24-Hours)",
            shift_time="07:00 AM to 07:00 AM",
            graph_base64=graph_base64
        )
    except Exception as e:
        logging.error(f"❌ Error rendering HTML: {e}", exc_info=True)
        raise

def send_email(email_html, graph_path):
    try:
        from_addr = os.getenv("EMAIL_SENDER")
        recipients = [email.strip() for email in os.getenv("EMAIL_RECIPIENTS", "").split(",")]
        password = os.getenv("EMAIL_PASSWORD")

        msg = MIMEMultipart("related")
        msg['Subject'] = f"🧾 24-Hour Furnace-3348 Wire Count Summary – {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = from_addr
        msg['To'] = ", ".join(recipients)

        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)
        msg_alternative.attach(MIMEText(email_html, "html"))

        with open(graph_path, 'rb') as f:
            image = MIMEApplication(f.read(), Name=os.path.basename(graph_path))
            image.add_header('Content-ID', '<graph1>')
            image.add_header('Content-Disposition', 'inline', filename=os.path.basename(graph_path))
            msg.attach(image)

        logging.info("📧 Sending 24hr email via Gmail SMTP...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_addr, password)
            server.sendmail(from_addr, recipients, msg.as_string())
        logging.info(f"✅ Email sent to: {', '.join(recipients)}")
        print("✅ Daily 24hr email sent")
    except Exception as e:
        logging.error(f"❌ Failed to send email: {e}", exc_info=True)
        raise

def send_24hr_report():
    try:
        logging.info("📩 Generating 24-hour report (7AM to 7AM)...")
        graph_dir = "Email_summary/output_graphs"
        os.makedirs(graph_dir, exist_ok=True)

        today = datetime.now().date()
        for fname in os.listdir(graph_dir):
            fpath = os.path.join(graph_dir, fname)
            if os.path.isfile(fpath):
                ftime = datetime.fromtimestamp(os.path.getmtime(fpath)).date()
                if ftime < today:
                    os.remove(fpath)

        df_summary, report_date = fetch_7am_to_7am_summary()
        graph_path = generate_24hr_wire_count_graph(df_summary.copy(), "24-Hour Summary", output_folder=graph_dir)
        graph_base64 = get_base64_image(graph_path)
        email_html = render_email_html(df_summary, report_date, graph_base64)
        send_email(email_html, graph_path)

    except Exception as e:
        logging.error(f"❌ Error in 24hr report: {e}", exc_info=True)

def schedule_daily_7am():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        send_24hr_report,
        'cron',
        hour=7,
        minute=0,
        id="daily_7am_report"
    )
    scheduler.start()
    logging.info("✅ Daily 7AM report scheduler started")
    print("✅ Scheduled daily 24-hour report at 7:00 AM")
    return scheduler

# ─── MAIN ───────────────────────────────
if __name__ == "__main__":
    logging.info("🚀 Starting 24hr summary scheduler...")
    send_24hr_report()  # Run immediately at script start
    scheduler = schedule_daily_7am()

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logging.warning("🛑 Scheduler stopped.")
        scheduler.shutdown()
