from plyer import notification


def show_notification(title: str, message: str, timeout: int = 10) -> None:
    """Show a Windows desktop toast notification."""
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="Laptop Guard",
            timeout=timeout,
        )
    except Exception as e:
        print(f"[-] Notification error: {e}")
