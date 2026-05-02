import struct

def parse_cdp(pkt):
    device = {}
    device["protocol"] = "CDP"

    try:
        raw = bytes(pkt)
        offset = 26

        while offset < len(raw) - 4:
            tlv_type = struct.unpack('!H', raw[offset:offset+2])[0]
            tlv_len = struct.unpack('!H', raw[offset+2:offset+4])[0]

            if tlv_len < 4:
                break

            value = raw[offset+4:offset+tlv_len]

            # Device hostname
            if tlv_type == 0x0001:
                device["name"] = value.decode("utf-8", errors="ignore")

            # IP Address
            elif tlv_type == 0x0002:
                if len(value) >= 9:
                    ip_bytes = value[5:9]
                    device["ip"] = f"{ip_bytes[0]}.{ip_bytes[1]}.{ip_bytes[2]}.{ip_bytes[3]}"

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