# delete_old_records.py

import psycopg2
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Database config
db_config = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

def delete_old_records():
    try:
        with psycopg2.connect(**db_config) as conn, conn.cursor() as cur:
            cur.execute("""
                DELETE FROM "3348_wire_count"
                WHERE timestamp < NOW() - INTERVAL '7 days';

            """)
            conn.commit()
            print("✅ Old records deleted successfully.")
    except Exception as e:
        print(f"❌ Error deleting old records: {e}")

if __name__ == "__main__":
    delete_old_records()
