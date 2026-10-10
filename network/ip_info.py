import socket
import secrets
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


# ── Native adapter configuration ─────────────────────────────────────────────

def get_ip_config(iface=None):
    """Read IP/DHCP metadata for exactly the adapter used by the scanners."""
    from network.platform_info import get_platform_ip_config

    selected = iface if iface is not None else conf.iface
    obj = selected if hasattr(selected, "network_name") else conf.ifaces.get(selected)
    name = getattr(obj, "network_name", None) or str(selected or "")
    result = get_platform_ip_config(name, getattr(obj, "ip", None),
                                    getattr(obj, "mac", None))
    result["interface"] = name
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


def get_dhcp_options(timeout=10, iface=None):
    """
    Send a DHCP INFORM packet and sniff the ACK to get full scope options.
    Returns a list of (option_number, label, value, flag) tuples.
    Falls back to an empty list if nothing is captured.
    Pass iface (scapy interface name) to bind to a specific adapter.
    """
    options = []

    try:
        iface = iface or _find_active_iface()
        my_ip  = get_if_addr(iface)
        my_mac = get_if_hwaddr(iface)

        if not my_ip or my_ip == "0.0.0.0":
            return options

        # Build a DHCP INFORM — tells the server we already have an IP,
        # please just send us the options
        xid = secrets.randbits(32)
        mac_bytes = bytes.fromhex(my_mac.replace(":", "").replace("-", ""))

        dhcp_inform = (
            Ether(dst="ff:ff:ff:ff:ff:ff", src=my_mac) /
            IP(src=my_ip, dst="255.255.255.255") /
            UDP(sport=68, dport=67) /
            BOOTP(
                op=1,
                xid=xid,
                ciaddr=my_ip,
                chaddr=mac_bytes
            ) /
            DHCP(options=[
                ("message-type", "inform"),
                ("param_req_list", [1, 3, 6, 12, 15, 28, 42, 43, 44,
                                     51, 54, 58, 59, 66, 67, 119, 121, 252]),
                "end"
            ])
        )

        def _is_dhcp_ack(pkt):
            return (
                pkt.haslayer(BOOTP) and pkt.haslayer(DHCP) and
                pkt[BOOTP].op == 2 and
                pkt[BOOTP].xid == xid and
                pkt[BOOTP].chaddr[:len(mac_bytes)] == mac_bytes and
                any(opt[0] == "message-type" and opt[1] == 5
                    for opt in pkt[DHCP].options
                    if isinstance(opt, tuple) and len(opt) > 1)
            )

        result = sniff(
            iface=iface,
            lfilter=_is_dhcp_ack,
            count=1,
            timeout=timeout,
            store=True,
            # Open the capture socket before sending, so a fast ACK is not lost.
            started_callback=lambda: sendp(dhcp_inform, iface=iface, verbose=False)
        )

        if not result:
            return options

        pkt = result[0]

        for opt in pkt[DHCP].options:
            if not isinstance(opt, tuple) or not opt or opt[0] == "end":
                continue
            opt_name_raw = opt[0]
            # Scapy expands multi-address options into (name, value1, value2, ...).
            opt_val      = opt[1:] if len(opt) > 2 else (opt[1] if len(opt) > 1 else "")

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
                    "classless_static_routes": 121,
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
