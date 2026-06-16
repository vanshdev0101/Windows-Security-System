import os
import pyotp
from dotenv import load_dotenv

load_dotenv()

def _get_or_create_totp_secret():
    secret = os.getenv("TOTP_SECRET", "").strip()
    if not secret:
        secret = pyotp.random_base32()
        print(f"\n[*] Generated new TOTP_SECRET: {secret}")
        print("[*] Add this to your .env file and also to Google Authenticator!\n")
    return secret

YOUR_EMAIL    = os.getenv("YOUR_EMAIL", "")
APP_PASSWORD  = os.getenv("APP_PASSWORD", "")
TOTP_SECRET   = _get_or_create_totp_secret()
SAVE_FOLDER   = os.getenv("SAVE_FOLDER", r"C:\IntruderPhotos")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 5))

os.makedirs(SAVE_FOLDER, exist_ok=True)
