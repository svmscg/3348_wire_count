import os
import time
import logging
import psycopg2
from datetime import datetime
from threading import Lock
from dotenv import load_dotenv
import sys

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_ideal_wire_count

# Load environment variables from .env
ENV_PATH = r"C:\Users\6078\Desktop\3348_wire_count\.env"
load_dotenv(dotenv_path=ENV_PATH)

# Database config
db_config = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Table name with quotes (PostgreSQL allows numeric names only when quoted)
TABLE_NAME = '"3348_wire_count"'


# ───── Ensure the table exists ─────
def create_table_if_not_exists():
    try:
        with psycopg2.connect(**db_config) as conn, conn.cursor() as cur:
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    id SERIAL PRIMARY KEY,
                    furnace_name VARCHAR(100),
                    lcg_wire_count INT,
                    pwlc_wire_count INT,
                    total_wire_count INT,
                    rtms INT,
                    mcid INT NOT NULL,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            print(f"✅ Table {TABLE_NAME} ensured.")
            logger.info(f"✅ Table {TABLE_NAME} ensured.")
    except Exception as e:
        logger.error(f"❌ Error creating table: {e}")


# ───── Insert a row into the table ─────
def insert_wire_count_data(furnace_name, lcg_wire, pwlc_wire, total_wire, rtms, mcid, timestamp):
    try:
        with psycopg2.connect(**db_config) as conn, conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {TABLE_NAME}
                (furnace_name, lcg_wire_count, pwlc_wire_count, total_wire_count, rtms, mcid, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (furnace_name, lcg_wire, pwlc_wire, total_wire, rtms, mcid, timestamp))
            conn.commit()
            logger.info(f"✅ Inserted → LCG: {lcg_wire}, PWLC: {pwlc_wire}, Total: {total_wire}")
            print(f"✅ Inserted → Furnace: {furnace_name}, LCG: {lcg_wire}, PWLC: {pwlc_wire}, Total: {total_wire}, RTMS: {rtms}, MCID: {mcid}, Timestamp: {timestamp}")
    except Exception as e:
        logger.error(f"❌ Insert failed: {e}")
        print(f"❌ Insert failed: {e}")


# ───── Periodic insert using shared result_dict ─────
def insert_to_db(result_dict, lock: Lock, mcid: int):
    logger.info("📓 DB Insert thread started")
    last_insert = datetime.now()

    while True:
        try:
            now = datetime.now()
            if (now - last_insert).total_seconds() >= 60:
                last_insert = now

                with lock:
                    snapshot = {
                        "LCG": result_dict.get("LCG", {}).copy(),
                        "PWLC": result_dict.get("PWLC", {}).copy()
                    }

                lcg = int(snapshot["LCG"].get("mode", 0))
                pwlc = int(snapshot["PWLC"].get("mode", 0))
                total = lcg + pwlc
                rtms_count = get_ideal_wire_count()

                logger.debug(f"📊 Mode counts → LCG: {lcg}, PWLC: {pwlc}, Total: {total}")
                logger.debug(f"🔄 RTMS Ideal Count: {rtms_count}")

                insert_wire_count_data(
                    furnace_name="Furnace-3348",
                    lcg_wire=lcg,
                    pwlc_wire=pwlc,
                    total_wire=total,
                    rtms=rtms_count,
                    mcid=mcid,
                    timestamp=now.replace(second=0, microsecond=0)
                )
        except Exception as e:
            logger.exception("❌ Error inserting into DB")

        time.sleep(5)


# ───── Ensure table on import ─────
create_table_if_not_exists()
