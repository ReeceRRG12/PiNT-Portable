"""Protocol regressions with synthetic packets; these tests send no traffic."""

import socket
import struct
import unittest
from unittest.mock import Mock, patch

from scapy.all import DNS, DNSRR, DNSRRSRV, IP, IPv6, UDP

from network.cdp_parser import parse_cdp
from network import mdns_scanner, snmp_query


def cdp_packet(addresses):
    """Ethernet / LLC SNAP / CDPv2 with an Address TLV."""
    value = struct.pack("!I", len(addresses)) + b"".join(addresses)
    tlv = struct.pack("!HH", 2, len(value) + 4) + value
    payload = b"\xaa\xaa\x03\x00\x00\x0c\x20\x00\x02\xb4\x00\x00" + tlv
    ethernet = bytes.fromhex("01000ccccccc020000000001") + struct.pack("!H", len(payload))
    return ethernet + payload


def cdp_address(protocol_type, protocol, address):
    return (bytes([protocol_type, len(protocol)]) + protocol +
            struct.pack("!H", len(address)) + address)


class CdpTests(unittest.TestCase):
    def test_ipv4_management_address(self):
        packet = cdp_packet([cdp_address(1, b"\xcc", socket.inet_aton("192.168.1.10"))])
        self.assertEqual(parse_cdp(packet)["ip"], "192.168.1.10")

    def test_ipv4_after_another_address_family(self):
        packet = cdp_packet([
            cdp_address(2, bytes.fromhex("aaaa0300000086dd"),
                        socket.inet_pton(socket.AF_INET6, "2001:db8::1")),
            cdp_address(1, b"\xcc", socket.inet_aton("10.20.30.40")),
        ])
        self.assertEqual(parse_cdp(packet)["ip"], "10.20.30.40")

    def test_truncated_address_is_not_reported(self):
        packet = cdp_packet([b"\x01\x01\xcc\x00\x04\xc0\xa8"])
        self.assertNotIn("ip", parse_cdp(packet))

    def test_truncated_tlv_is_not_reported(self):
        packet = cdp_packet([cdp_address(1, b"\xcc", socket.inet_aton("192.168.1.10"))])
        self.assertNotIn("ip", parse_cdp(packet[:-1]))


class SnmpTests(unittest.TestCase):
    # SNMPv2c response: public, request 1, sysDescr.0 = "test".
    RESPONSE = bytes.fromhex(
        "302a02010104067075626c6963a21d020101020100020100"
        "3012301006082b06010201010100040474657374")

    def test_get_uses_selected_wire_version(self):
        for version in (0, 1):
            with self.subTest(version=version):
                sock = Mock()
                sock.recvfrom.return_value = (self.RESPONSE, ("192.0.2.1", 161))
                with patch.object(snmp_query.socket, "socket", return_value=sock):
                    self.assertEqual(snmp_query.snmp_get(
                        "192.0.2.1", "public", "1.3.6.1.2.1.1.1.0", version=version),
                        ("test", None))
                packet = sock.sendto.call_args.args[0]
                self.assertEqual(packet[2:5], bytes([2, 1, version]))
                sock.close.assert_called_once()

    def test_walk_uses_selected_wire_version(self):
        for version in (0, 1):
            with self.subTest(version=version):
                sock = Mock()
                sock.recvfrom.side_effect = [
                    (self.RESPONSE, ("192.0.2.1", 161)), socket.timeout()]
                rows = []
                with patch.object(snmp_query.socket, "socket", return_value=sock):
                    snmp_query.snmp_walk(
                        "192.0.2.1", "public", "1.3.6.1.2.1.1", version=version,
                        row_callback=lambda *row: rows.append(row))
                self.assertEqual(rows, [("1.3.6.1.2.1.1.1.0", "test", None)])
                for call in sock.sendto.call_args_list:
                    self.assertEqual(call.args[0][2:5], bytes([2, 1, version]))
                sock.close.assert_called_once()

    def test_malformed_oids_return_errors_without_opening_socket(self):
        for oid in ("hello", "1", "1.3.a", "1.-3.6", "3.1", "1.40.1", "1..3", ""):
            with self.subTest(oid=oid), patch.object(snmp_query.socket, "socket") as factory:
                value, error = snmp_query.snmp_get("192.0.2.1", "public", oid)
                self.assertIsNone(value)
                self.assertIn("Invalid OID", error)
                errors = []
                snmp_query.snmp_walk("192.0.2.1", "public", oid,
                                     row_callback=lambda *row: errors.append(row))
                self.assertEqual(len(errors), 1)
                self.assertIn("Invalid OID", errors[0][2])
                factory.assert_not_called()


class MdnsTests(unittest.TestCase):
    INSTANCE = "Office Printer._ipp._tcp.local."

    def scan_packets(self, packets):
        results = []

        def sniff_packets(**kwargs):
            self.assertEqual(kwargs["iface"], "test-adapter")
            for packet in packets:
                kwargs["prn"](packet)

        # Prevent query workers starting; sniff is replaced with fixture replay.
        with patch.object(mdns_scanner.threading, "Thread"), \
                patch.object(mdns_scanner, "sniff", side_effect=sniff_packets):
            mdns_scanner.scan_mdns(results.extend, timeout=1, iface="test-adapter")
        return results

    def test_proxy_source_is_replaced_by_srv_target_address(self):
        packet = IP(src="192.168.1.1") / UDP(sport=5353, dport=5353) / DNS(
            qr=1, an=[DNSRR(rrname="_ipp._tcp.local.", type="PTR", rdata=self.INSTANCE)],
            ar=[
                DNSRRSRV(rrname=self.INSTANCE, port=631, target="PRINTER.local."),
                DNSRR(rrname="printer.local.", type="A", rdata="192.168.1.90"),
            ])
        # Reparse the wire packet to exercise Scapy's actual DNS record representation.
        devices = self.scan_packets([IP(bytes(packet))])
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["ip"], "192.168.1.90")

    def test_target_address_can_arrive_in_later_packet(self):
        discovery = IP(src="192.168.1.1") / UDP(sport=5353, dport=5353) / DNS(
            qr=1, an=[DNSRR(rrname="_ipp._tcp.local.", type="PTR", rdata=self.INSTANCE)],
            ar=[DNSRRSRV(rrname=self.INSTANCE, port=631, target="printer.local.")])
        address = IP(src="192.168.1.1") / UDP(sport=5353, dport=5353) / DNS(
            qr=1, an=[DNSRR(rrname="printer.local.", type="A", rdata="192.168.1.90")])
        devices = self.scan_packets([IP(bytes(discovery)), IP(bytes(address))])
        self.assertEqual(devices[0]["ip"], "192.168.1.90")

    def test_ipv6_target_address_is_used(self):
        packet = IPv6(src="2001:db8::1") / UDP(sport=5353, dport=5353) / DNS(
            qr=1, an=[DNSRR(rrname="_ipp._tcp.local.", type="PTR", rdata=self.INSTANCE)],
            ar=[
                DNSRRSRV(rrname=self.INSTANCE, port=631, target="printer.local."),
                DNSRR(rrname="printer.local.", type="AAAA", rdata="2001:db8::90"),
            ])
        devices = self.scan_packets([IPv6(bytes(packet))])
        self.assertEqual(devices[0]["ip"], "2001:db8::90")

    def test_source_address_remains_fallback(self):
        packet = IP(src="192.168.1.90") / UDP(sport=5353, dport=5353) / DNS(
            qr=1, an=[DNSRR(rrname="_ipp._tcp.local.", type="PTR", rdata=self.INSTANCE)])
        self.assertEqual(self.scan_packets([IP(bytes(packet))])[0]["ip"], "192.168.1.90")

    def test_capture_failure_reports_error_without_success(self):
        success, error = Mock(), Mock()
        with patch.object(mdns_scanner.threading, "Thread"), \
                patch.object(mdns_scanner, "sniff", side_effect=PermissionError("denied")):
            mdns_scanner.scan_mdns(success, error_callback=error)
        success.assert_not_called()
        error.assert_called_once()
        self.assertTrue(error.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
