import re

def parse_lldp(pkt):
    raw = bytes(pkt)
    device = {}
    device["protocol"] = "LLDP"

    match = re.search(b'\x0a.([\x20-\x7e]+)', raw)
    if match:
        device["name"] = match.group(1).decode("utf-8", errors="ignore")

    match = re.search(b'gigabitEthernet\\s[\\d/]+', raw, re.IGNORECASE)
    if match:
        device["port"] = match.group(0).decode("utf-8", errors="ignore")

    match = re.search(b'\x0c.([\x20-\x7e]{10,})', raw)
    if match:
        device["description"] = match.group(1).decode("utf-8", errors="ignore")

    match = re.search(b'\x10\x0c\x05\x01(....)', raw)
    if match:
        ip_bytes = match.group(1)
        device["ip"] = f"{ip_bytes[0]}.{ip_bytes[1]}.{ip_bytes[2]}.{ip_bytes[3]}"

    match = re.search(b'\xfe\x12\x00\x80\xc2\x03\x00\x01.(..)', raw)
    if match:
        vlan_bytes = match.group(1)
        device["vlan"] = (vlan_bytes[0] << 8) + vlan_bytes[1]

    return device