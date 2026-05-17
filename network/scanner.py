import threading
from scapy.all import sniff
from network.lldp_parser import parse_lldp
from network.cdp_parser import parse_cdp

def scan(callback, timeout=30, iface=None):
    result = {}
    stop_event = threading.Event()

    def lldp_handler(pkt):
        if not stop_event.is_set():
            device = parse_lldp(pkt)
            if device:
                stop_event.set()
                result.update(device)
                callback(result)

    def cdp_handler(pkt):
        if not stop_event.is_set():
            device = parse_cdp(pkt)
            if device:
                stop_event.set()
                result.update(device)
                callback(result)

    sniff_kwargs_lldp = {
        "filter": "ether proto 0x88cc",
        "prn": lldp_handler,
        "store": 0,
        "timeout": timeout,
    }
    sniff_kwargs_cdp = {
        "filter": "ether dst 01:00:0c:cc:cc:cc",
        "prn": cdp_handler,
        "store": 0,
        "timeout": timeout,
    }
    if iface:
        sniff_kwargs_lldp["iface"] = iface
        sniff_kwargs_cdp["iface"]  = iface

    # Start LLDP listener thread
    lldp_thread = threading.Thread(
        target=sniff,
        kwargs=sniff_kwargs_lldp,
        daemon=True
    )

    # Start CDP listener thread
    cdp_thread = threading.Thread(
        target=sniff,
        kwargs=sniff_kwargs_cdp,
        daemon=True
    )

    lldp_thread.start()
    cdp_thread.start()
    lldp_thread.join()
    cdp_thread.join()

    if not result:
        callback(None)