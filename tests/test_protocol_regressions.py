"""Offline protocol edge cases; sockets and capture are always replaced."""

import socket
import struct
import unittest
from unittest.mock import Mock, patch

from network import scanner, snmp_query
from network.lldp_parser import parse_lldp


def response(oid):
    varbind = snmp_query._ber_tlv(
        0x30, snmp_query._ber_oid(oid) + snmp_query._ber_str("value"))
    pdu = snmp_query._ber_tlv(
        0xA2, snmp_query._ber_int(1) + snmp_query._ber_int(0) +
        snmp_query._ber_int(0) + snmp_query._ber_tlv(0x30, varbind))
    return snmp_query._ber_tlv(
        0x30, snmp_query._ber_int(1) + snmp_query._ber_str("public") + pdu)


class SnmpRegressions(unittest.TestCase):
    def walk(self, base, oids):
        sock = Mock()
        sock.recvfrom.side_effect = [
            (response(oid), ("192.0.2.1", 161)) for oid in oids
        ] + [socket.timeout()]
        rows = []
        with patch.object(snmp_query.socket, "socket", return_value=sock):
            snmp_query.snmp_walk("192.0.2.1", "public", base,
                                 row_callback=lambda *row: rows.append(row))
        sock.close.assert_called_once()
        return rows, sock

    def test_oid_first_subidentifier_can_span_multiple_bytes(self):
        # 2.999 combines to 1079, BER-encoded as 0x88 0x37.
        self.assertEqual(snmp_query._decode_oid(bytes.fromhex("883703")), "2.999.3")

    def test_oid_second_arc_can_exceed_39_under_root_two(self):
        self.assertEqual(snmp_query._decode_oid(bytes.fromhex("7803")), "2.40.3")

    def test_truncated_oid_is_rejected(self):
        for raw in (b"", b"\x2b\x81", b"\x88"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                snmp_query._decode_oid(raw)

    def test_walk_stays_within_oid_arc_boundary(self):
        rows, sock = self.walk("1.3.6.1.2.1.1", ["1.3.6.1.2.1.10.1"])
        self.assertEqual(rows, [])
        self.assertEqual(sock.sendto.call_count, 1)

    def test_walk_accepts_normalized_base_oid(self):
        rows, _ = self.walk(" .1.3.6.1.2.1.1. ", ["1.3.6.1.2.1.1.1.0"])
        self.assertEqual(rows, [("1.3.6.1.2.1.1.1.0", "value", None)])

    def test_walk_stops_at_backwards_response(self):
        rows, sock = self.walk("1.3.6.1", ["1.3.6.1.9", "1.3.6.1.8", "1.3.6.1.9"])
        self.assertEqual(rows, [("1.3.6.1.9", "value", None)])
        self.assertEqual(sock.sendto.call_count, 2)

    def test_walk_compares_numeric_arcs(self):
        rows, _ = self.walk("1.3.6.1", ["1.3.6.1.9", "1.3.6.1.10"])
        self.assertEqual([row[0] for row in rows], ["1.3.6.1.9", "1.3.6.1.10"])

    def test_truncated_response_does_not_report_partial_value(self):
        sock = Mock()
        sock.recvfrom.return_value = (response("1.3.6.1.2.1.1.1.0")[:-1], ("192.0.2.1", 161))
        with patch.object(snmp_query.socket, "socket", return_value=sock):
            value, error = snmp_query.snmp_get("192.0.2.1", "public", "1.3.6.1.2.1.1.1.0")
        self.assertIsNone(value)
        self.assertTrue(error)
        sock.close.assert_called_once()


def lldp_packet(description):
    def tlv(kind, value):
        return struct.pack("!H", kind << 9 | len(value)) + value
    return (bytes.fromhex("0180c200000e02000000000188cc") +
            tlv(5, b"switch") + tlv(6, description) + tlv(2, b"\x05eth0") + b"\x00\x00")


class LldpRegressions(unittest.TestCase):
    def test_empty_description_preserves_remaining_fields(self):
        for description in (b"", b" \n\t"):
            with self.subTest(description=description):
                device = parse_lldp(lldp_packet(description))
                self.assertEqual(device["name"], "switch")
                self.assertEqual(device["port"], "eth0")
                self.assertEqual(device["description"], "")

    def test_scan_completes_for_empty_description(self):
        def replay(**kwargs):
            kwargs["prn"](lldp_packet(b""))
        success, error = Mock(), Mock()
        with patch.object(scanner, "sniff", side_effect=replay):
            scanner.scan(success, error_callback=error)
        error.assert_not_called()
        success.assert_called_once()
        self.assertEqual(success.call_args.args[0]["name"], "switch")


if __name__ == "__main__":
    unittest.main()
