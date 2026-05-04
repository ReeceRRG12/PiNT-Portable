import struct

def parse_lldp(pkt):
    raw = bytes(pkt)
    device = {"protocol": "LLDP"}

    pos = 14  # skip Ethernet header

    port_from_type2 = None  # fallback
    port_from_type4 = None  # preferred

    while pos + 2 <= len(raw):
        header = struct.unpack_from("!H", raw, pos)[0]
        tlv_type = (header >> 9) & 0x7F
        tlv_len  = header & 0x1FF
        pos += 2

        if tlv_type == 0:
            break
        if pos + tlv_len > len(raw):
            break

        value = raw[pos: pos + tlv_len]
        pos += tlv_len

        if tlv_type == 2:  # Port ID
            subtype = value[0] if value else 0
            port_str = value[1:].decode("utf-8", errors="ignore").strip()
            # Only use if subtype is ifname (5) or locally-assigned (7)
            # Ignore subtype 3 (MAC address) and subtype 4 (network address)
            if subtype in (5, 7) and port_str:
                port_from_type2 = port_str

        elif tlv_type == 4:  # Port Description — always preferred
            port_from_type4 = value.decode("utf-8", errors="ignore").strip()

        elif tlv_type == 5:  # System Name
            device["name"] = value.decode("utf-8", errors="ignore").strip()

        elif tlv_type == 6:  # System Description
            raw_desc = value.decode("utf-8", errors="ignore").strip()
            # Trim kernel strings — take only the first line
            device["description"] = raw_desc.splitlines()[0][:80]

        elif tlv_type == 8:  # Management Address
            if len(value) >= 6 and value[1] == 1:  # subtype 1 = IPv4
                ip_bytes = value[2:6]
                device["ip"] = f"{ip_bytes[0]}.{ip_bytes[1]}.{ip_bytes[2]}.{ip_bytes[3]}"

        elif tlv_type == 127:  # Organizationally Specific
            if len(value) < 4:
                continue
            oui     = value[0:3]
            subtype = value[3]
            # IEEE 802.1 OUI = 00:80:c2, subtype 1 = Port VLAN ID
            if oui == b'\x00\x80\xc2' and subtype == 0x01 and len(value) >= 6:
                device["vlan"] = struct.unpack_from("!H", value, 4)[0]

    # Port: prefer type 4 (description), fall back to type 2 (ID)
    device["port"] = port_from_type4 or port_from_type2 or "Unknown"

    return device