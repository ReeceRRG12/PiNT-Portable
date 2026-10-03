from scapy.all import sniff

from network.capture import capture_error_message
from network.lldp_parser import parse_lldp
from network.cdp_parser import parse_cdp


def scan(callback, timeout=30, iface=None, error_callback=None):
    """Capture both protocols and complete once, with no leftover listeners."""
    result = {}

    def handle(pkt):
        raw = bytes(pkt)
        if len(raw) < 14:
            return
        if raw[12:14] == b"\x88\xcc":
            device = parse_lldp(pkt)
        elif raw[:6] == b"\x01\x00\x0c\xcc\xcc\xcc":
            device = parse_cdp(pkt)
        else:
            return
        if device and any(device.get(k) not in (None, "", "Unknown")
                          for k in ("name", "port", "ip", "chassis")):
            result.update(device)

    kwargs = dict(
        filter="ether proto 0x88cc or ether dst 01:00:0c:cc:cc:cc",
        prn=handle, stop_filter=lambda pkt: bool(result), store=False,
        timeout=timeout,
    )
    if iface:
        kwargs["iface"] = iface
    try:
        sniff(**kwargs)
    except Exception as exc:
        if error_callback:
            error_callback(capture_error_message(exc))
            return
        raise
    callback(result or None)
