import socket
import ipaddress

from scapy.all import ARP, Ether, srp, get_if_addr, conf
import psutil


def get_subnet_for_iface(iface):
    """
    Return the network CIDR string (e.g. '192.168.1.0/24') for the given
    Scapy interface name, or None if it cannot be determined.
    """
    try:
        ip = get_if_addr(iface) if iface else get_if_addr(conf.iface)
        if not ip or ip in ("0.0.0.0", ""):
            return None

        # Walk psutil adapters to find the matching netmask
        for addrs in psutil.net_if_addrs().values():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address == ip:
                    network = ipaddress.IPv4Network(
                        f"{ip}/{addr.netmask}", strict=False)
                    return str(network)

        # Fallback: assume /24
        parts = ip.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"

    except Exception:
        return None


def scan_arp(network, iface=None, timeout=3, callback=None):
    """
    ARP-sweep *network* (CIDR string, e.g. '192.168.1.0/24').

    Calls callback(results) when complete where results is a list of dicts:
        {"ip": str, "mac": str, "hostname": str}
    sorted by IP address.
    """
    try:
        packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network)
        kwargs = {"timeout": timeout, "verbose": False}
        if iface:
            kwargs["iface"] = iface

        answered, _ = srp(packet, **kwargs)

        results = []
        for _, received in answered:
            ip  = received.psrc
            mac = received.hwsrc.upper()
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except Exception:
                hostname = ""
            results.append({"ip": ip, "mac": mac, "hostname": hostname})

        results.sort(key=lambda x: ipaddress.ip_address(x["ip"]))

    except Exception:
        results = []

    if callback:
        callback(results)
    return results
