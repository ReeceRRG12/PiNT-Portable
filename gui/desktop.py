"""Launch management connections using the host's desktop tools."""

import ipaddress
import os
import re
import shutil
import subprocess
import sys


def management_address(value):
    """Accept only IP literals received from discovery packets."""
    address = ipaddress.ip_address(value)
    scope = getattr(address, "scope_id", None)
    if scope and not re.fullmatch(r"[A-Za-z0-9_.-]+", scope):
        raise ValueError("Invalid address scope")
    return str(address)


def _find_putty():
    found = shutil.which("putty")
    if found:
        return found
    for candidate in (
        r"C:\Program Files\PuTTY\putty.exe",
        r"C:\Program Files (x86)\PuTTY\putty.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\PuTTY\putty.exe"),
        os.path.join(os.environ.get("APPDATA", ""), r"PuTTY\putty.exe"),
    ):
        if os.path.isfile(candidate):
            return candidate
    return None


def launch_terminal(protocol, host):
    host = management_address(host)
    if protocol not in ("ssh", "telnet"):
        raise ValueError("Unsupported connection type")
    if sys.platform == "darwin":
        if protocol == "telnet" and not shutil.which("telnet"):
            raise RuntimeError("Telnet is not installed. Use SSH or install a Telnet client.")
        url_host = f"[{host}]" if ":" in host else host
        subprocess.run(["/usr/bin/open", "-a", "Terminal", f"{protocol}://{url_host}"],
                       check=True, capture_output=True, timeout=5)
    elif sys.platform == "win32":
        putty = _find_putty()
        if putty:
            subprocess.Popen([putty, f"-{protocol}", host])
            return
        program = shutil.which(protocol)
        if not program:
            raise RuntimeError(f"Install PuTTY or enable the Windows {protocol.upper()} client.")
        subprocess.Popen([program, host], creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        raise RuntimeError(f"Open a terminal and run: {protocol} {host}")
