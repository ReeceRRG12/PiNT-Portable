"""
Minimal SNMP v1/v2c client using raw UDP sockets.
No external dependencies — works on Python 3.12+.
"""

import socket
import os

PYSNMP_AVAILABLE = True   # always True — no external library needed

# ── Common OID presets ────────────────────────────────────────────────────────

COMMON_OIDS = {
    "System Description":  "1.3.6.1.2.1.1.1.0",
    "System Name":         "1.3.6.1.2.1.1.5.0",
    "System Location":     "1.3.6.1.2.1.1.6.0",
    "System Contact":      "1.3.6.1.2.1.1.4.0",
    "System Uptime":       "1.3.6.1.2.1.1.3.0",
    "Interface Count":     "1.3.6.1.2.1.2.1.0",
    "Interface Table":     "1.3.6.1.2.1.2.2",
    "ARP Table":           "1.3.6.1.2.1.4.22",
    "Routing Table":       "1.3.6.1.2.1.4.21",
    "LLDP Remote Table":   "1.0.8802.1.1.2.1.4",
}


# ── BER encoding ──────────────────────────────────────────────────────────────

def _ber_len(n):
    if n < 0x80:
        return bytes([n])
    b = []
    while n:
        b.append(n & 0xff)
        n >>= 8
    b.reverse()
    return bytes([0x80 | len(b)]) + bytes(b)


def _ber_tlv(tag, data):
    return bytes([tag]) + _ber_len(len(data)) + data


def _ber_int(n):
    if n == 0:
        return _ber_tlv(0x02, b'\x00')
    b = []
    while n > 0:
        b.append(n & 0xff)
        n >>= 8
    b.reverse()
    if b[0] & 0x80:
        b.insert(0, 0x00)
    return _ber_tlv(0x02, bytes(b))


def _ber_str(s):
    return _ber_tlv(0x04, s.encode() if isinstance(s, str) else s)


def _ber_null():
    return b'\x05\x00'


def _base128(n):
    if n == 0:
        return [0]
    b = []
    while n:
        b.append(n & 0x7f)
        n >>= 7
    b.reverse()
    for i in range(len(b) - 1):
        b[i] |= 0x80
    return b


def _ber_oid(oid_str):
    parts = list(map(int, oid_str.strip('.').split('.')))
    enc = _base128(40 * parts[0] + parts[1])
    for p in parts[2:]:
        enc += _base128(p)
    return _ber_tlv(0x06, bytes(enc))


def _build_packet(pdu_tag, request_id, community, oid):
    varbind  = _ber_tlv(0x30, _ber_oid(oid) + _ber_null())
    varbinds = _ber_tlv(0x30, varbind)
    pdu = _ber_tlv(pdu_tag,
                   _ber_int(request_id) +
                   _ber_int(0) +   # error-status
                   _ber_int(0) +   # error-index
                   varbinds)
    return _ber_tlv(0x30,
                    _ber_int(1) +   # version 1 = SNMPv2c
                    _ber_str(community) +
                    pdu)


# ── BER decoding ──────────────────────────────────────────────────────────────

def _parse_len(data, off):
    first = data[off]; off += 1
    if first & 0x80 == 0:
        return first, off
    nb = first & 0x7f
    n = 0
    for _ in range(nb):
        n = (n << 8) | data[off]; off += 1
    return n, off


def _parse_tlv(data, off):
    tag = data[off]; off += 1
    length, off = _parse_len(data, off)
    return tag, data[off:off + length], off + length


def _decode_oid(raw):
    parts = [raw[0] // 40, raw[0] % 40]
    i, n = 1, 0
    while i < len(raw):
        b = raw[i]; i += 1
        n = (n << 7) | (b & 0x7f)
        if b & 0x80 == 0:
            parts.append(n); n = 0
    return '.'.join(map(str, parts))


def _decode_value(tag, raw):
    if tag == 0x02:                     # Integer
        n = int.from_bytes(raw, 'big', signed=True)
        return str(n)
    if tag == 0x04:                     # OctetString
        try:
            return raw.decode('utf-8').rstrip('\x00')
        except Exception:
            return raw.hex()
    if tag == 0x05:                     # Null
        return 'NULL'
    if tag == 0x06:                     # OID
        return _decode_oid(raw)
    if tag == 0x40:                     # IpAddress
        return '.'.join(str(b) for b in raw) if len(raw) == 4 else raw.hex()
    if tag in (0x41, 0x42, 0x46):      # Counter32 / Gauge32 / Counter64
        labels = {0x41: 'Counter32', 0x42: 'Gauge32', 0x46: 'Counter64'}
        return f"{int.from_bytes(raw, 'big')} ({labels[tag]})"
    if tag == 0x43:                     # TimeTicks
        t = int.from_bytes(raw, 'big')
        s = t // 100
        return f"{s // 86400}d {(s % 86400) // 3600}h {(s % 3600) // 60}m {s % 60}s"
    if tag in (0x80, 0x81, 0x82):      # noSuchObject / noSuchInstance / endOfMibView
        return {0x80: '(noSuchObject)', 0x81: '(noSuchInstance)',
                0x82: '(endOfMibView)'}[tag]
    return f"0x{raw.hex()} (tag={tag:#04x})"


def _parse_response(data):
    """Return list of (oid_str, value_str) from a raw SNMP response."""
    _, msg, _ = _parse_tlv(data, 0)        # outer SEQUENCE
    off = 0
    _, _, off = _parse_tlv(msg, off)        # version
    _, _, off = _parse_tlv(msg, off)        # community
    _, pdu, _ = _parse_tlv(msg, off)        # response PDU

    poff = 0
    _, _, poff = _parse_tlv(pdu, poff)      # request-id
    _, err_raw, poff = _parse_tlv(pdu, poff)
    _, _, poff = _parse_tlv(pdu, poff)      # error-index

    err = int.from_bytes(err_raw, 'big')
    if err:
        raise ValueError(f"SNMP error-status {err}")

    _, varbinds, _ = _parse_tlv(pdu, poff)

    results = []
    voff = 0
    while voff < len(varbinds):
        _, vb, voff = _parse_tlv(varbinds, voff)
        oid_tag, oid_raw, inner = _parse_tlv(vb, 0)
        val_tag, val_raw, _    = _parse_tlv(vb, inner)
        results.append((_decode_oid(oid_raw), _decode_value(val_tag, val_raw)))
    return results


# ── Public API ────────────────────────────────────────────────────────────────

def snmp_get(host, community, oid, port=161, version=1, timeout=3):
    """
    SNMP GET a single OID.  Returns (value_str, error_str).
    version arg is accepted for API compatibility but v2c is always used.
    """
    req_id = os.getpid() & 0xFFFF
    packet = _build_packet(0xA0, req_id, community, oid)   # GetRequest
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(packet, (host, port))
        data, _ = sock.recvfrom(65535)
        results = _parse_response(data)
        return (results[0][1], None) if results else (None, "Empty response")
    except socket.timeout:
        return None, f"Timeout — no response from {host}:{port}"
    except Exception as exc:
        return None, str(exc)
    finally:
        sock.close()


def snmp_walk(host, community, base_oid, port=161, version=1,
              timeout=3, row_callback=None):
    """
    SNMP WALK from base_oid using repeated GetNext requests.

    row_callback(oid_str, value_str, error_str) — error_str is None on success.
    """
    current = base_oid
    req_id  = os.getpid() & 0xFFFF
    sock    = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        while True:
            req_id = (req_id + 1) & 0xFFFF
            packet = _build_packet(0xA1, req_id, community, current)  # GetNext
            sock.sendto(packet, (host, port))
            data, _ = sock.recvfrom(65535)
            results = _parse_response(data)
            if not results:
                break
            oid_str, val_str = results[0]
            if not oid_str.startswith(base_oid):
                break
            if val_str in ('(endOfMibView)', '(noSuchObject)', '(noSuchInstance)'):
                break
            if oid_str == current:      # guard against infinite loop
                break
            if row_callback:
                row_callback(oid_str, val_str, None)
            current = oid_str
    except socket.timeout:
        pass                            # normal end-of-walk
    except Exception as exc:
        if row_callback:
            row_callback(None, None, str(exc))
    finally:
        sock.close()
