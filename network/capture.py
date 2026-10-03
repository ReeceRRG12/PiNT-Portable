"""Actionable packet-capture errors shared by scanner panels."""

import sys


def capture_error_message(error):
    detail = str(error).strip() or type(error).__name__
    lower = detail.lower()
    permission_error = isinstance(error, PermissionError) or any(
        word in lower for word in ("permission", "access denied", "not permitted", "bpf")
    )
    if sys.platform == "darwin" and permission_error:
        return ("Packet capture access is required. Set up macOS capture permissions "
                "as described in the README, then retry.")
    if sys.platform == "win32" and (permission_error or "pcap" in lower):
        return ("Packet capture is unavailable. Check Npcap installation and "
                "your account's capture permissions, then retry.")
    return f"Capture failed: {detail}. Check the selected adapter and its capture access."
