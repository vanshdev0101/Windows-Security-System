# Laptop Guard

A Windows intrusion monitoring application that detects failed login attempts, captures webcam evidence, generates time-based OTP codes, sends email alerts, and provides a real-time monitoring dashboard.

---

## Overview

Laptop Guard monitors the Windows Security Event Log for failed authentication events (Event ID 4625).

When a failed login attempt is detected, the application:

* Captures a webcam photo
* Displays a desktop notification
* Generates a TOTP verification code
* Sends an email alert containing the timestamp, OTP, and captured image
* Stores evidence locally for later review

The project is intended for personal workstation monitoring, security experimentation, and educational cybersecurity projects.

---

## Features

### Event Monitoring

* Monitors Windows Security Event Logs
* Detects failed login events (Event ID 4625)
* Configurable polling interval

### Evidence Collection

* Captures images from the default webcam
* Automatically timestamps captured photos
* Stores images locally

### Alerting

* Windows desktop notifications
* Email alerts via Gmail SMTP
* Attached webcam evidence
* Time-based OTP generation

### Dashboard

* Live OTP display
* OTP countdown indicator
* Intruder photo gallery
* Full-size image preview
* Security event history
* Activity log viewer
* Service status monitoring

### Configuration

* Environment-variable based configuration
* Automatic TOTP secret generation
* Custom photo storage location

---

## Architecture

```text
Failed Login Attempt
          │
          ▼
Windows Security Log
(Event ID 4625)
          │
          ▼
Laptop Guard Monitor
          │
 ┌────────┼────────┬────────┐
 ▼        ▼        ▼        ▼
Photo   Notify    OTP     Email
Capture User   Generate   Alert
          │
          ▼
   Evidence Storage
          │
          ▼
 Dashboard Update
```

---

## Project Structure

```text
laptop-guard/
│
├── main.py
├── dashboard.py
├── config.py
│
├── guard/
│   ├── camera.py
│   ├── event_monitor.py
│   ├── notifier.py
│   ├── mailer.py
│   └── otp_manager.py
│
├── .env.example
├── requirements.txt
├── guard.log
└── README.md
```

---

## Requirements

* Windows 10 or Windows 11
* Python 3.10+
* Administrator privileges
* Webcam
* Gmail account with App Password enabled

---

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/laptop-guard.git

cd laptop-guard
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a configuration file:

```bash
copy .env.example .env
```

Edit `.env`:

```env
YOUR_EMAIL=you@gmail.com
APP_PASSWORD=your_app_password

TOTP_SECRET=

SAVE_FOLDER=C:\IntruderPhotos

POLL_INTERVAL=5
```

---

## Gmail Configuration

Laptop Guard uses Gmail SMTP for email delivery.

1. Enable Two-Factor Authentication.
2. Generate a Gmail App Password.
3. Add the generated password to the `.env` file.

Do not use your normal Gmail password.

---

## Running the Monitor

Launch an elevated terminal and run:

```bash
python main.py
```

Administrator privileges are required to access the Windows Security Event Log.

---

## Running the Dashboard

```bash
python dashboard.py
```

The dashboard provides:

* Evidence review
* OTP monitoring
* Activity logging
* Service status visibility

---

## OTP Setup

If no TOTP secret is provided, Laptop Guard automatically generates one on first launch.

Example:

```text
Generated new TOTP_SECRET: XXXXXXXXXXXXXXXXX
```

Store this value in your `.env` file and optionally import it into:

* Google Authenticator
* Authy
* Microsoft Authenticator

Generated codes remain valid for 30 seconds.

---

## Evidence Storage

Captured images are stored in:

```text
C:\IntruderPhotos
```

File naming format:

```text
intruder_YYYYMMDD_HHMMSS.jpg
```

Example:

```text
intruder_20250120_221530.jpg
```

---

## Example Alert

```text
FAILED LOGIN ALERT

Time     : 2025-01-20 22:15:30
OTP Code : 573921

If this login attempt was not initiated by you,
review the attached image and investigate immediately.
```

---

## Dependencies

| Package       | Purpose                   |
| ------------- | ------------------------- |
| opencv-python | Webcam capture            |
| pywin32       | Windows Event Log access  |
| plyer         | Desktop notifications     |
| pyotp         | TOTP generation           |
| python-dotenv | Environment configuration |
| pillow        | Dashboard image rendering |

---

## Limitations

* Windows-only implementation
* Polling-based event monitoring
* Gmail SMTP dependency
* Local storage only
* No automatic evidence retention policy
* Single-recipient email configuration

---

## Security Notes

* Never commit `.env` to source control.
* Do not expose `APP_PASSWORD` or `TOTP_SECRET`.
* Run only on systems you own or are authorized to monitor.
* Protect stored evidence appropriately.

---

## Future Improvements

* Telegram notifications
* Discord integration
* Face recognition
* Cloud evidence storage
* Multi-user support
* Event subscription monitoring instead of polling
* Remote dashboard access

---

## License

MIT License

```
```
