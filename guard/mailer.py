import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from config import YOUR_EMAIL, APP_PASSWORD


def send_alert_email(photo_path: str | None, otp: str, timestamp: str) -> None:
    """Send an alert email with the intruder photo and OTP."""
    if not YOUR_EMAIL or not APP_PASSWORD:
        print("[-] Email not configured. Skipping email alert.")
        return

    msg = MIMEMultipart()
    msg["From"]    = YOUR_EMAIL
    msg["To"]      = YOUR_EMAIL
    msg["Subject"] = f"⚠️ Failed Login on Your Laptop — {timestamp}"

    body = f"""
⚠️  LAPTOP GUARD — FAILED LOGIN ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Time     : {timestamp}
OTP Code : {otp}
           (Time-based — valid for 30 seconds)

If this was YOU — use the OTP above to confirm it's you.
If this was NOT you — someone is trying to access your laptop!

A photo from your webcam has been attached.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sent by Laptop Guard
"""
    msg.attach(MIMEText(body, "plain"))

    if photo_path and os.path.exists(photo_path):
        with open(photo_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(photo_path)}"
            )
            msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(YOUR_EMAIL, APP_PASSWORD)
            server.sendmail(YOUR_EMAIL, YOUR_EMAIL, msg.as_string())
        print("[+] Alert email sent successfully.")
    except smtplib.SMTPAuthenticationError:
        print("[-] Email auth failed. Check YOUR_EMAIL and APP_PASSWORD in .env")
    except Exception as e:
        print(f"[-] Email error: {e}")
