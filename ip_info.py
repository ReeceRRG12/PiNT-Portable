import subprocess
import re
import socket
from scapy.all import (
    sniff, sendp, Ether, IP, UDP, BOOTP, DHCP,
    conf, get_if_list, get_if_hwaddr, get_if_addr
)

# ── DHCP Option definitions ───────────────────────────────────────────────────

DHCP_OPTIONS = {
    1:  ("Subnet Mask",          "standard"),
    3:  ("Router / Gateway",     "standard"),
    6:  ("DNS Servers",          "standard"),
    12: ("Hostname",             "standard"),
    15: ("Domain Name",          "standard"),
    28: ("Broadcast Address",    "standard"),
    42: ("NTP Servers",          "notable"),
    43: ("Vendor Specific",      "notable"),
    44: ("WINS Servers",         "notable"),
    51: ("Lease Time",           "standard"),
    54: ("DHCP Server",          "standard"),
    58: ("Renewal Time (T1)",    "standard"),
    59: ("Rebinding Time (T2)",  "standard"),
    66: ("TFTP Server",          "notable"),
    67: ("Bootfile Name",        "notable"),
    119: ("Domain Search List",  "standard"),
    121: ("Classless Static Routes", "notable"),
    252: ("WPAD (Proxy)",        "notable"),
}

FLAG_COLOURS = {
    "standard": "#00ff88",   # green
    "notable":  "#ffaa00",   # amber
    "unknown":  "#ff4757",   # red
}


# ── ipconfig /all parser ──────────────────────────────────────────────────────

def get_ip_config():
    """
    Run ipconfig /all and return a dict of the active adapter's details.
    Picks the adapter that has a default gateway set.
    """
    result = {
        "adapter":      "Unknown",
        "ip":           "Unknown",
        "subnet":       "Unknown",
        "gateway":      "Unknown",
        "dns":          [],
        "dhcp_server":  "Unknown",
        "dhcp_enabled": False,
        "lease_obtained": "Unknown",
        "lease_expires":  "Unknown",
        "mac":          "Unknown",
        "hostname":     "Unknown",
        "domain":       "Unknown",
    }

    try:
        raw = subprocess.check_output(
            ["ipconfig", "/all"],
            encoding="utf-8",
            errors="ignore",
            creationflags=0x08000000   # CREATE_NO_WINDOW
        )
    except Exception as e:
        result["error"] = str(e)
        return result

    # Hostname is at the top before adapter blocks
    m = re.search(r"Host Name[.\s]+:\s*(.+)", raw)
    if m:
        result["hostname"] = m.group(1).strip()

    # Split into adapter blocks
    blocks = re.split(r"\r?\n(?=\S)", raw)

    for block in blocks:
        # We want the block that has a Default Gateway entry
        if "Default Gateway" not in block:
            continue
        gw_match = re.search(r"Default Gateway[.\s]+:\s*([\d.]+)", block)
        if not gw_match:
            continue

        result["gateway"] = gw_match.group(1).strip()

        m = re.search(r"^(.+?)\s+adapter\s+(.+?):", block, re.MULTILINE)
        if m:
            result["adapter"] = m.group(2).strip()

        m = re.search(r"Physical Address[.\s]+:\s*([\w-]+)", block)
        if m:
            result["mac"] = m.group(1).strip()

        m = re.search(r"DHCP Enabled[.\s]+:\s*(\w+)", block)
        if m:
            result["dhcp_enabled"] = m.group(1).strip().lower() == "yes"

        m = re.search(r"IPv4 Address[.\s]+:\s*([\d.]+)", block)
        if m:
            result["ip"] = m.group(1).strip()

        m = re.search(r"Subnet Mask[.\s]+:\s*([\d.]+)", block)
        if m:
            result["subnet"] = m.group(1).strip()

        m = re.search(r"DHCP Server[.\s]+:\s*([\d.]+)", block)
        if m:
            result["dhcp_server"] = m.group(1).strip()

        m = re.search(r"Lease Obtained[.\s]+:\s*(.+)", block)
        if m:
            result["lease_obtained"] = m.group(1).strip()

        m = re.search(r"Lease Expires[.\s]+:\s*(.+)", block)
        if m:
            result["lease_expires"] = m.group(1).strip()

        m = re.search(r"Connection-specific DNS Suffix[.\s]+:\s*(.+)", block)
        if m:
            result["domain"] = m.group(1).strip()

        dns_servers = re.findall(r"DNS Servers[.\s]+:\s*([\d.]+)", block)
        extra_dns   = re.findall(r"^\s+([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})\s*$",
                                  block, re.MULTILINE)
        result["dns"] = dns_servers + extra_dns

        break   # found the active adapter — stop

    return result


# ── DHCP option sniffer ───────────────────────────────────────────────────────

def _find_active_iface():
    """Return the Scapy interface name that has a non-loopback IPv4 address."""
    for iface in get_if_list():
        try:
            addr = get_if_addr(iface)
            if addr and not addr.startswith("127.") and addr != "0.0.0.0":
                return iface
        except Exception:
            continue
    return conf.iface


def get_dhcp_options(timeout=10):
    """
    Send a DHCP INFORM packet and sniff the ACK to get full scope options.
    Returns a list of (option_number, label, value, flag) tuples.
    Falls back to an empty list if nothing is captured.
    """
    options = []

    try:
        iface = _find_active_iface()
        my_ip  = get_if_addr(iface)
        my_mac = get_if_hwaddr(iface)

        if not my_ip or my_ip == "0.0.0.0":
            return options

        # Build a DHCP INFORM — tells the server we already have an IP,
        # please just send us the options
        xid = 0xdeadbeef

        dhcp_inform = (
            Ether(dst="ff:ff:ff:ff:ff:ff", src=my_mac) /
            IP(src=my_ip, dst="255.255.255.255") /
            UDP(sport=68, dport=67) /
            BOOTP(
                op=1,
                xid=xid,
                ciaddr=my_ip,
                chaddr=bytes.fromhex(my_mac.replace(":", "").replace("-", ""))
            ) /
            DHCP(options=[
                ("message-type", "inform"),
                ("param_req_list", [1, 3, 6, 12, 15, 28, 42, 43, 44,
                                     51, 54, 58, 59, 66, 67, 119, 121, 252]),
                "end"
            ])
        )

        captured = []

        def _is_dhcp_ack(pkt):
            return (
                pkt.haslayer(DHCP) and
                pkt[BOOTP].xid == xid and
                any(opt[0] == "message-type" and opt[1] == 5
                    for opt in pkt[DHCP].options
                    if isinstance(opt, tuple))
            )

        sendp(dhcp_inform, iface=iface, verbose=False)
        result = sniff(
            iface=iface,
            lfilter=_is_dhcp_ack,
            count=1,
            timeout=timeout,
            store=True
        )

        if not result:
            return options

        pkt = result[0]

        for opt in pkt[DHCP].options:
            if not isinstance(opt, tuple) or opt[0] == "end":
                continue
            opt_name_raw = opt[0]
            opt_val      = opt[1] if len(opt) > 1 else ""

            # Scapy returns some options by name, others by number
            # Try to get the numeric code
            try:
                opt_num = int(opt_name_raw)
            except (ValueError, TypeError):
                # Map Scapy name → number for the ones we care about
                name_to_num = {
                    "subnet_mask": 1, "router": 3, "name_server": 6,
                    "hostname": 12, "domain": 15, "broadcast_address": 28,
                    "NTP_server": 42, "vendor_specific": 43,
                    "NetBIOS_name_server": 44, "lease_time": 51,
                    "server_id": 54, "renewal_time": 58, "rebinding_time": 59,
                    "TFTP_server_name": 66, "bootfile_name": 67,
                    "message-type": None,
                }
                opt_num = name_to_num.get(opt_name_raw)
                if opt_num is None:
                    continue

            label, flag = DHCP_OPTIONS.get(opt_num, (f"Option {opt_num}", "unknown"))

            # Format the value into something readable
            value = _format_option_value(opt_num, opt_val)

            options.append((opt_num, label, value, flag))

        options.sort(key=lambda x: x[0])

    except Exception as e:
        options.append((0, "Error", str(e), "unknown"))

    return options


def _format_option_value(opt_num, raw):
    """Turn raw Scapy option values into human-readable strings."""
    try:
        if isinstance(raw, (list, tuple)):
            return ", ".join(_format_single(v) for v in raw)
        if opt_num in (51, 58, 59):   # time values in seconds
            secs = int(raw)
            if secs >= 86400:
                return f"{secs // 86400}d {(secs % 86400) // 3600}h"
            elif secs >= 3600:
                return f"{secs // 3600}h {(secs % 3600) // 60}m"
            else:
                return f"{secs // 60}m"
        return _format_single(raw)
    except Exception:
        return str(raw)


def _format_single(v):
    if isinstance(v, bytes):
        try:
            return v.decode("utf-8").strip("\x00")
        except Exception:
            return v.hex()
    try:
        socket.inet_ntoa(v.to_bytes(4, "big") if isinstance(v, int) else v)
        return socket.inet_ntoa(v)
    except Exception:
        pass
    return str(v)