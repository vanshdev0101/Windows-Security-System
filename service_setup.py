"""
Laptop Guard — Windows Service Setup
Run this as Administrator to install/uninstall the background service via NSSM.
"""

import os
import sys
import subprocess
import urllib.request
import zipfile

PROJECT_DIR  = os.path.dirname(os.path.abspath(__file__))
NSSM_DIR     = os.path.join(PROJECT_DIR, "nssm")
NSSM_EXE     = os.path.join(NSSM_DIR, "nssm.exe")
NSSM_URL     = "https://nssm.cc/release/nssm-2.24.zip"
NSSM_ZIP     = os.path.join(PROJECT_DIR, "nssm.zip")
SERVICE_NAME = "LaptopGuard"
PYTHON_EXE   = sys.executable
MAIN_SCRIPT  = os.path.join(PROJECT_DIR, "main.py")
LOG_FILE     = os.path.join(PROJECT_DIR, "guard.log")


def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def download_nssm():
    if os.path.exists(NSSM_EXE):
        print("[*] NSSM already present.")
        return True
    print("[*] Downloading NSSM...")
    try:
        urllib.request.urlretrieve(NSSM_URL, NSSM_ZIP)
        print("[*] Extracting NSSM...")
        with zipfile.ZipFile(NSSM_ZIP, "r") as z:
            for member in z.namelist():
                # grab win64 nssm.exe only
                if "win64/nssm.exe" in member:
                    z.extract(member, PROJECT_DIR)
                    extracted = os.path.join(PROJECT_DIR, member)
                    os.makedirs(NSSM_DIR, exist_ok=True)
                    os.replace(extracted, NSSM_EXE)
                    break
        os.remove(NSSM_ZIP)
        # clean up leftover nssm folder
        leftover = os.path.join(PROJECT_DIR, "nssm-2.24")
        if os.path.exists(leftover):
            import shutil
            shutil.rmtree(leftover)
        print(f"[+] NSSM ready at: {NSSM_EXE}")
        return True
    except Exception as e:
        print(f"[-] Failed to download NSSM: {e}")
        print("    Download manually from https://nssm.cc/download")
        print(f"    Place nssm.exe at: {NSSM_EXE}")
        return False


def install_service():
    if not is_admin():
        print("[-] Please run this script as Administrator.")
        return

    if not download_nssm():
        return

    print(f"\n[*] Installing '{SERVICE_NAME}' as a Windows Service...")

    cmds = [
        [NSSM_EXE, "install",    SERVICE_NAME, PYTHON_EXE, MAIN_SCRIPT],
        [NSSM_EXE, "set",        SERVICE_NAME, "AppDirectory",   PROJECT_DIR],
        [NSSM_EXE, "set",        SERVICE_NAME, "DisplayName",    "Laptop Guard Security"],
        [NSSM_EXE, "set",        SERVICE_NAME, "Description",    "Monitors failed logins and captures webcam photos."],
        [NSSM_EXE, "set",        SERVICE_NAME, "Start",          "SERVICE_AUTO_START"],
        [NSSM_EXE, "set",        SERVICE_NAME, "AppStdout",      LOG_FILE],
        [NSSM_EXE, "set",        SERVICE_NAME, "AppStderr",      LOG_FILE],
        [NSSM_EXE, "set",        SERVICE_NAME, "AppRestartDelay","5000"],
    ]

    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[-] Command failed: {' '.join(cmd)}")
            print(f"    {result.stderr.strip()}")
            return

    # Start the service
    result = subprocess.run([NSSM_EXE, "start", SERVICE_NAME],
                            capture_output=True, text=True)
    if result.returncode == 0:
        print(f"\n[+] Service '{SERVICE_NAME}' installed and started!")
        print(f"[+] Logs: {LOG_FILE}")
        print(f"[+] It will auto-start on every Windows boot.")
        print(f"\n    To check status: sc query LaptopGuard")
        print(f"    To stop:         sc stop LaptopGuard")
        print(f"    To uninstall:    python service_setup.py uninstall")
    else:
        print(f"[-] Service installed but failed to start: {result.stderr.strip()}")
        print(f"    Try: sc start {SERVICE_NAME}")


def uninstall_service():
    if not is_admin():
        print("[-] Please run this script as Administrator.")
        return

    print(f"[*] Stopping and removing '{SERVICE_NAME}'...")
    subprocess.run([NSSM_EXE, "stop",   SERVICE_NAME], capture_output=True)
    result = subprocess.run([NSSM_EXE, "remove", SERVICE_NAME, "confirm"],
                            capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[+] Service '{SERVICE_NAME}' removed successfully.")
    else:
        print(f"[-] Failed to remove: {result.stderr.strip()}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("install", "uninstall"):
        print("Usage:")
        print("  python service_setup.py install    ← install & start service")
        print("  python service_setup.py uninstall  ← stop & remove service")
        sys.exit(1)

    if sys.argv[1] == "install":
        install_service()
    else:
        uninstall_service()
