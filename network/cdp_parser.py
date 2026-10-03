import struct


def _parse_ipv4_address(value):
    """Read IPv4 from a CDP Address TLV's counted, variable-length entries."""
    if len(value) < 4:
        return None
    count = struct.unpack_from('!I', value)[0]
    pos = 4
    for _ in range(count):
        if pos + 2 > len(value):
            break
        protocol_type, protocol_len = value[pos:pos + 2]
        pos += 2
        if pos + protocol_len + 2 > len(value):
            break
        protocol = value[pos:pos + protocol_len]
        pos += protocol_len
        address_len = struct.unpack_from('!H', value, pos)[0]
        pos += 2
        if pos + address_len > len(value):
            break
        address = value[pos:pos + address_len]
        pos += address_len
        # NLPID 0xcc identifies IPv4; other address families may precede it.
        if protocol_type == 1 and protocol == b'\xcc' and address_len == 4:
            return '.'.join(str(octet) for octet in address)
    return None


def parse_cdp(pkt):
    device = {}
    device["protocol"] = "CDP"

    try:
        raw = bytes(pkt)
        offset = 26

        while offset < len(raw) - 4:
            tlv_type = struct.unpack('!H', raw[offset:offset+2])[0]
            tlv_len = struct.unpack('!H', raw[offset+2:offset+4])[0]

            if tlv_len < 4 or offset + tlv_len > len(raw):
                break

            value = raw[offset+4:offset+tlv_len]

            # Device hostname
            if tlv_type == 0x0001:
                device["name"] = value.decode("utf-8", errors="ignore")

            # IP Address
            elif tlv_type == 0x0002:
                ip = _parse_ipv4_address(value)
                if ip:
                    device["ip"] = ip

            # Port ID
            elif tlv_type == 0x0003:
                device["port"] = value.decode("utf-8", errors="ignore")

            # Software version
            elif tlv_type == 0x0005:
                device["description"] = value.decode("utf-8", errors="ignore").split('\n')[0]

            # Platform / Model
            elif tlv_type == 0x0006:
                device["model"] = value.decode("utf-8", errors="ignore")

            offset += tlv_len

    except Exception as e:
        print(f"CDP parse error: {e}")

    return device
