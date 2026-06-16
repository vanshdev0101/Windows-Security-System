"""
Laptop Guard — main entry point.
Run as Administrator for Event Log access.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import time
import datetime
from config import POLL_INTERVAL
from guard.event_monitor import get_failed_login_count
from guard.camera import capture_photo
from guard.notifier import show_notification
from guard.mailer import send_alert_email
from guard.otp_manager import generate_otp


def monitor():
    print("=" * 50)
    print("  [GUARD] Laptop Guard - Started")
    print(f"  Polling every {POLL_INTERVAL}s for failed logins")
    print("  Press Ctrl+C to stop")
    print("=" * 50)

    last_count = get_failed_login_count()

    while True:
        time.sleep(POLL_INTERVAL)
        current_count = get_failed_login_count()

        if current_count > last_count:
            diff = current_count - last_count
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[!] {diff} failed login attempt(s) detected at {timestamp}")

            # 1. Desktop notification
            show_notification(
                "⚠️ Laptop Guard Alert",
                f"{diff} failed login attempt(s) detected!\nCheck your email for photo + OTP."
            )

            # 2. Capture intruder photo
            photo_path = capture_photo()

            # 3. Generate OTP
            otp = generate_otp()
            print(f"[*] OTP: {otp}  (valid 30 seconds)")

            # 4. Email alert with photo + OTP
            send_alert_email(photo_path, otp, timestamp)

            last_count = current_count


if __name__ == "__main__":
    monitor()