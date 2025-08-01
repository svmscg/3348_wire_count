# clear_logs.py

log_files = [
    r"C:\Users\6078\Desktop\3348_wire_count\logs\Email_summary.log",
    r"C:\Users\6078\Desktop\3348_wire_count\logs\telegram.log",
    r"C:\Users\6078\Desktop\3348_wire_count\logs\wire_count.log",
]

for log_file in log_files:
    try:
        with open(log_file, 'w') as file:
            file.write("")  # Clear contents
        print(f"✅ Cleared: {log_file}")
    except Exception as e:
        print(f"❌ Failed to clear {log_file}: {e}")
