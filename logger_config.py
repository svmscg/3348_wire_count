# logger_config.py
import logging
import os
from datetime import datetime

# ───── Create logs directory ─────
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# ───── Use fixed log file ─────
log_file = os.path.join(log_dir,r"C:\Users\6078\Desktop\3348_wire_count\logs\wire_count.log")

# ───── Create logger instance ─────
logger = logging.getLogger("wire_logger")
logger.setLevel(logging.DEBUG)  # Allow DEBUG and above

# ───── Clear previous handlers to avoid double logs ─────
if logger.hasHandlers():
    logger.handlers.clear()

# ───── File Handler ─────
file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8', delay=False)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# ───── Console Handler ─────
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# ───── Force flush every time ─────
class FlushOnLogHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

file_handler.flush = lambda: None  # Manually flush if needed later
