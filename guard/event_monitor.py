import win32evtlog


def get_failed_login_count() -> int:
    """
    Read the Windows Security Event Log and count Event ID 4625 entries.
    Event 4625 = An account failed to log on.
    Requires the script to be run as Administrator.
    """
    try:
        hand = win32evtlog.OpenEventLog("localhost", "Security")
        flags = (
            win32evtlog.EVENTLOG_BACKWARDS_READ
            | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        )
        count = 0
        events = win32evtlog.ReadEventLog(hand, flags, 0)
        for event in events:
            if event.EventID == 4625:
                count += 1
        win32evtlog.CloseEventLog(hand)
        return count
    except Exception as e:
        print(f"[-] Event log read error: {e}")
        print("    Make sure you are running this script as Administrator.")
        return 0
