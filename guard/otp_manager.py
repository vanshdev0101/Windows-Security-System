import pyotp
from config import TOTP_SECRET


def generate_otp() -> str:
    """Generate a time-based OTP (valid 30 seconds) using the TOTP secret."""
    totp = pyotp.TOTP(TOTP_SECRET)
    return totp.now()


def verify_otp(code: str) -> bool:
    """Verify a user-provided OTP code."""
    totp = pyotp.TOTP(TOTP_SECRET)
    return totp.verify(code)
