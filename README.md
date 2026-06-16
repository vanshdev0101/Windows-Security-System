# 🔒 Laptop Guard

A lightweight Windows security tool that monitors failed login attempts, captures a webcam photo of the intruder, sends a desktop notification, and emails you an OTP alert — all automatically.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📸 Intruder Photo | Captures webcam photo on every failed login |
| 🔔 Desktop Alert | Instant Windows toast notification |
| 🔑 OTP Code | Time-based OTP (TOTP) sent to your email |
| 📧 Email Alert | Photo + OTP delivered to your Gmail |

---

## 🗂️ Project Structure

```
laptop-guard/
├── main.py               ← Entry point
├── config.py             ← Loads .env settings
├── guard/
│   ├── camera.py         ← Webcam capture
│   ├── event_monitor.py  ← Windows Event Log watcher
│   ├── notifier.py       ← Desktop notifications
│   ├── mailer.py         ← Gmail alert sender
│   └── otp_manager.py    ← TOTP generation & verification
├── .env.example          ← Template — copy to .env
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/laptop-guard.git
cd laptop-guard
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your `.env`

```bash
copy .env.example .env
```

Edit `.env` with your values:

```env
YOUR_EMAIL=you@gmail.com
APP_PASSWORD=xxxx xxxx xxxx xxxx
TOTP_SECRET=                      # Leave blank to auto-generate
SAVE_FOLDER=C:\IntruderPhotos
POLL_INTERVAL=5
```

> **Gmail App Password:** Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) → Generate a password for "Mail". Use that instead of your real Gmail password.

### 4. Run as Administrator

Right-click PowerShell → **Run as Administrator**, then:

```bash
python main.py
```

> Administrator access is required to read the Windows Security Event Log.

---

## 🚀 Auto-start on Boot (Optional)

1. Create a file called `start_guard.bat`:
   ```bat
   @echo off
   pythonw C:\path\to\laptop-guard\main.py
   ```

2. Press `Win + R` → type `shell:startup` → press Enter

3. Paste `start_guard.bat` into the Startup folder

Laptop Guard will now silently run every time you log in.

---

## 🔑 TOTP / Google Authenticator (Optional)

On first run, if `TOTP_SECRET` is blank, the script auto-generates one and prints it:

```
[*] Generated new TOTP_SECRET: JBSWY3DPEHPK3PXP
[*] Add this to your .env file and also to Google Authenticator!
```

You can add this secret to **Google Authenticator** or **Authy** to see live OTP codes on your phone — the same codes the script emails you.

---

## 📸 How It Works

```
Wrong password entered
        │
        ▼
Windows logs Event ID 4625
        │
        ▼
Laptop Guard detects new failed event
        │
        ├──▶ 📸 Webcam photo captured
        ├──▶ 🔔 Desktop notification shown
        ├──▶ 🔑 TOTP OTP generated
        └──▶ 📧 Email sent with photo + OTP
```

---

## 🛡️ Privacy & Safety

- Photos are saved **locally** to `SAVE_FOLDER` and **never uploaded** anywhere except your own email
- Your `.env` file (with credentials) is **gitignored** and never pushed to GitHub
- The `TOTP_SECRET` in `.env` is private — do not share it

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `opencv-python` | Webcam capture |
| `pywin32` | Windows Event Log access |
| `plyer` | Desktop notifications |
| `pyotp` | TOTP OTP generation |
| `python-dotenv` | `.env` config loading |

---

## ⚠️ Requirements

- **Windows 10/11** only (uses Windows Security Event Log)
- **Python 3.10+**
- **Must run as Administrator**
- A working **webcam**
- A **Gmail account** with App Passwords enabled

---

## 📄 License

MIT License — free to use, modify, and distribute for personal use.
