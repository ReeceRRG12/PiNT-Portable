import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Port presets ──────────────────────────────────────────────────────────────

TOP_20 = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139,
    143, 443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080,
]

TOP_100 = sorted(set([
    1, 7, 9, 13, 21, 22, 23, 25, 26, 37, 53, 79, 80, 81, 88,
    106, 110, 111, 113, 119, 135, 139, 143, 144, 179, 199,
    389, 427, 443, 444, 445, 465, 513, 514, 515, 543, 544,
    548, 554, 587, 631, 646, 873, 990, 993, 995,
    1025, 1026, 1027, 1028, 1029, 1110, 1433, 1720, 1723, 1755,
    1900, 2000, 2001, 2049, 2121, 2717, 3000, 3128, 3306, 3389,
    3986, 4899, 5000, 5009, 5051, 5060, 5101, 5190, 5357, 5432,
    5631, 5666, 5800, 5900, 5985, 6000, 6001, 6646, 7070,
    8000, 8008, 8009, 8080, 8081, 8443, 8888, 9100, 9999,
    10000, 32768, 49152, 49153, 49154, 49155, 49156, 49157,
]))

WEB = [80, 443, 8080, 8443, 8000, 8008, 8081, 8888, 9000, 9001]

PRESET_LABELS = ["Top 20", "Top 100", "Web", "Custom"]

PRESET_PORTS = {
    "Top 20": TOP_20,
    "Top 100": TOP_100,
    "Web":    WEB,
}

# ── Service name hints ────────────────────────────────────────────────────────

SERVICE_NAMES = {
    21:    "FTP",
    22:    "SSH",
    23:    "Telnet",
    25:    "SMTP",
    53:    "DNS",
    67:    "DHCP",
    80:    "HTTP",
    88:    "Kerberos",
    110:   "POP3",
    111:   "RPC",
    135:   "MS-RPC",
    139:   "NetBIOS",
    143:   "IMAP",
    161:   "SNMP",
    179:   "BGP",
    389:   "LDAP",
    443:   "HTTPS",
    445:   "SMB",
    465:   "SMTPS",
    514:   "Syslog",
    515:   "LPD/Print",
    587:   "SMTP-Auth",
    631:   "IPP",
    636:   "LDAPS",
    873:   "rsync",
    990:   "FTPS",
    993:   "IMAPS",
    995:   "POP3S",
    1433:  "MSSQL",
    1720:  "H.323",
    1723:  "PPTP",
    3306:  "MySQL",
    3389:  "RDP",
    5432:  "PostgreSQL",
    5900:  "VNC",
    5985:  "WinRM",
    6379:  "Redis",
    8080:  "HTTP-Alt",
    8443:  "HTTPS-Alt",
    9100:  "Printing",
    27017: "MongoDB",
}


# ── Scanner ───────────────────────────────────────────────────────────────────

def scan_ports(host, ports, timeout=1.0,
               progress_callback=None, done_callback=None):
    """
    TCP connect-scan *ports* on *host*.

    progress_callback(completed: int, total: int) — called from background
    threads; callers must marshal to the UI thread if needed.

    done_callback(results: list[dict]) — called from the background thread
    when the scan finishes.  Each dict: {"port": int, "service": str}.
    """
    open_ports = []
    total      = len(ports)
    completed  = 0

    def _check(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return port if result == 0 else None
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=min(200, len(ports) or 1)) as ex:
        futures = {ex.submit(_check, p): p for p in ports}
        for future in as_completed(futures):
            completed += 1
            port = future.result()
            if port is not None:
                open_ports.append({
                    "port":    port,
                    "service": SERVICE_NAMES.get(port, ""),
                })
            if progress_callback:
                progress_callback(completed, total)

    open_ports.sort(key=lambda x: x["port"])

    if done_callback:
        done_callback(open_ports)
    return open_ports
