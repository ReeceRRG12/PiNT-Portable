from scapy.all import sniff, DNS, IP, IPv6
import re
import socket
import threading

def clean_friendly_name(name, service_type):
    name = name.rstrip(".")
    name = re.sub(r'\.local$', '', name, flags=re.IGNORECASE)
    if "@" in name:
        name = name.split("@", 1)[1]
    name = re.sub(r'HomePodSensor\s+\d+', 'HomePod', name)
    name = name.strip(".")
    return name.strip()

def clean_service_type(stype):
    stype = stype.rstrip(".")
    stype = re.sub(r'\.local$', '', stype, flags=re.IGNORECASE)
    return stype

def strip_local(name):
    return re.sub(r'\.local\.?$', '', name.rstrip("."), flags=re.IGNORECASE)

def normalise(name):
    name = name.lower()
    name = re.sub(r'\s*\((\d+)\)', r' \1', name)
    name = name.replace('-', ' ').strip()
    return name

SIMPLE_SERVICE_TYPES = {
    "_airplay._tcp",
    "_raop._tcp",
    "_googlecast._tcp",
    "_spotify-connect._tcp",
    "_http._tcp",
    "_printer._tcp",
    "_ipp._tcp",
    "_smb._tcp",
    "_afpovertcp._tcp",
    "_ssh._tcp",
    "_sftp-ssh._tcp",
}

ALWAYS_HIDDEN_SERVICE_TYPES = {
    "_services._dns-sd._udp",
    "_sleep-proxy._udp",
    "_meshcop._udp",
    "_asquic._udp",
}

MDNS_ADDR = "224.0.0.251"
MDNS_PORT = 5353


def _iter_records(section):
    """Support Scapy's DNS record lists and older payload-linked records."""
    records = section if isinstance(section, (list, tuple)) else (section,)
    for rr in records:
        while rr is not None and hasattr(rr, "type"):
            yield rr
            rr = getattr(rr, "payload", None)


def _dns_name(value):
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    return strip_local(str(value)).casefold()


def send_mdns_queries(queries):
    for q in queries:
        try:
            qname = b""
            for part in q.rstrip(".").split("."):
                qname += bytes([len(part)]) + part.encode()
            qname += b"\x00"
            header = b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00"
            question = qname + b"\x00\x0c\x00\x01"
            packet = header + question
            for _ in range(2):
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
                sock.sendto(packet, (MDNS_ADDR, MDNS_PORT))
                sock.close()
        except Exception as e:
            print(f"Send error for {q}: {e}")

def scan_mdns(callback, timeout=30, iface=None, error_callback=None):
    devices = {}
    host_ip_map = {}
    srv_map = {}
    stopped = threading.Event()

    queries = [
        "_airplay._tcp.local",
        "_raop._tcp.local",
        "_companion-link._tcp.local",
        "_hap._tcp.local",
        "_googlecast._tcp.local",
        "_http._tcp.local",
        "_printer._tcp.local",
        "_smb._tcp.local",
        "_sftp-ssh._tcp.local",
    ]

    def delayed_queries():
        for delay in (2, 10, 10):
            if stopped.wait(delay):
                return
            send_mdns_queries(queries)

    query_thread = threading.Thread(target=delayed_queries, daemon=True)
    query_thread.start()

    def parse_rr_chain(section):
        for rr in _iter_records(section):
            try:
                rrname = _dns_name(rr.rrname)
                if rr.type == 1 and hasattr(rr, 'rdata'):
                    host_ip_map[rrname] = rr.rdata
                elif rr.type == 28 and hasattr(rr, 'rdata'):
                    # Keep an IPv4 address when both families are advertised.
                    host_ip_map.setdefault(rrname, rr.rdata)
                elif rr.type == 33 and hasattr(rr, 'target'):
                    srv_map[rrname] = _dns_name(rr.target)
            except Exception:
                continue

    def handle_packet(pkt):
        try:
            if not pkt.haslayer(DNS):
                return
            src_ip = None
            if pkt.haslayer(IP):
                src_ip = pkt[IP].src
            elif pkt.haslayer(IPv6):
                src_ip = pkt[IPv6].src
            dns = pkt[DNS]
            for section in ['an', 'ar', 'ns']:
                try:
                    parse_rr_chain(getattr(dns, section))
                except Exception:
                    pass
            for rr in _iter_records(dns.an):
                try:
                    if rr.type == 12:
                        raw = (rr.rdata.decode("utf-8", errors="ignore")
                               if isinstance(rr.rdata, bytes) else str(rr.rdata))
                        rrname = (rr.rrname.decode("utf-8", errors="ignore")
                                  if isinstance(rr.rrname, bytes) else str(rr.rrname))
                        service_type = rrname.rstrip(".").replace(".local.", "").replace(".local", "")
                        if service_type in ALWAYS_HIDDEN_SERVICE_TYPES:
                            continue
                        friendly_raw = raw.replace(f".{rrname.rstrip('.')}", "").strip(".")
                        if not friendly_raw:
                            friendly_raw = raw
                        friendly = clean_friendly_name(friendly_raw, service_type)
                        stype_display = clean_service_type(service_type)
                        instance = strip_local(raw)
                        key = raw
                        if key not in devices:
                            devices[key] = {
                                "friendly": friendly,
                                "type": stype_display,
                                "ip": src_ip or "Unknown",
                                "raw": raw,
                                "simple": service_type in SIMPLE_SERVICE_TYPES,
                                "instance": instance
                            }
                        elif src_ip and devices[key]["ip"] == "Unknown":
                            devices[key]["ip"] = src_ip
                except Exception:
                    pass
        except Exception as e:
            print(f"mDNS parse error: {e}")

    sniff_kwargs = {"filter": "udp port 5353", "prn": handle_packet,
                    "timeout": timeout, "store": False}
    if iface:
        sniff_kwargs["iface"] = iface
    try:
        sniff(**sniff_kwargs)
    except Exception as exc:
        if error_callback is None:
            raise
        from network.capture import capture_error_message
        error_callback(capture_error_message(exc))
        return
    finally:
        stopped.set()

    _resolve_ips(devices, host_ip_map, srv_map)
    callback(list(devices.values()))


def _resolve_ips(devices, host_ip_map, srv_map):
    host_ip_map = {_dns_name(k): v for k, v in host_ip_map.items()}
    srv_map = {_dns_name(k): _dns_name(v) for k, v in srv_map.items()}
    norm_ip_map = {normalise(k): v for k, v in host_ip_map.items()}
    for key, device in devices.items():
        # SRV/A/AAAA describe the service host, which may differ from a
        # proxy or Bonjour gateway that sent the packet. Prefer those records.
        instance = _dns_name(device.get("instance", ""))
        if instance in srv_map:
            hostname = srv_map[instance]
            if hostname in host_ip_map:
                device["ip"] = host_ip_map[hostname]
                continue
        if instance in host_ip_map:
            device["ip"] = host_ip_map[instance]
            continue
        if device.get("ip") not in (None, "Unknown"):
            continue
        friendly = device.get("friendly", "")
        norm_friendly = normalise(friendly)
        if norm_friendly in norm_ip_map:
            device["ip"] = norm_ip_map[norm_friendly]

