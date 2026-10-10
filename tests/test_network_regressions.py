"""Offline DHCP and TCP regressions; packet I/O and sockets are mocked."""
import unittest
from unittest.mock import MagicMock, patch

from scapy.all import BOOTP, DHCP, Ether, IP, UDP

from network import ip_info, port_scanner


class DhcpOptionRegressionTests(unittest.TestCase):
    MAC = "00:11:22:33:44:55"
    MAC_BYTES = bytes.fromhex("001122334455")
    XID = 12345

    def setUp(self):
        for target, value in (("get_if_addr", "192.0.2.2"),
                              ("get_if_hwaddr", self.MAC),
                              ("secrets.randbits", self.XID)):
            patcher = patch("network.ip_info." + target, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def ack(self, options=None, **bootp):
        fields = dict(op=2, xid=self.XID, chaddr=self.MAC_BYTES)
        fields.update(bootp)
        packet = (Ether(src="00:aa:bb:cc:dd:ee", dst=self.MAC) /
                  IP(src="192.0.2.1", dst="192.0.2.2") /
                  UDP(sport=67, dport=68) / BOOTP(**fields) /
                  DHCP(options=[("message-type", 5)] + (options or []) + ["end"]))
        return Ether(bytes(packet))

    def test_capture_is_ready_before_inform_is_sent(self):
        with patch.object(ip_info, "sendp") as send:
            def receive(**kwargs):
                send.assert_not_called()
                self.assertIn("started_callback", kwargs)
                kwargs["started_callback"]()
                send.assert_called_once()
                sent = send.call_args.args[0]
                self.assertEqual(sent[BOOTP].xid, self.XID)
                self.assertEqual(send.call_args.kwargs["iface"], "test-interface")
                self.assertTrue(kwargs["lfilter"](self.ack()))
                return []

            with patch.object(ip_info, "sniff", side_effect=receive):
                self.assertEqual(ip_info.get_dhcp_options(iface="test-interface"), [])

    def test_ack_must_match_transaction_and_client(self):
        def receive(**kwargs):
            accept = kwargs["lfilter"]
            self.assertTrue(accept(self.ack()))
            self.assertFalse(accept(self.ack(xid=self.XID + 1)))
            self.assertFalse(accept(self.ack(chaddr=bytes.fromhex("aabbccddeeff"))))
            self.assertFalse(accept(self.ack(op=1)))
            self.assertFalse(accept(Ether() / IP()))
            self.assertFalse(accept(DHCP(options=[("message-type", 5)])))
            malformed = BOOTP(op=2, xid=self.XID, chaddr=self.MAC_BYTES) / DHCP(
                options=[(), ("message-type",)])
            self.assertFalse(accept(malformed))
            return []

        with patch.object(ip_info, "sniff", side_effect=receive), patch.object(ip_info, "sendp"):
            self.assertEqual(ip_info.get_dhcp_options(iface="test-interface"), [])

    def test_all_dns_and_router_addresses_and_routes_are_preserved(self):
        packet = self.ack([
            ("name_server", "192.0.2.53", "198.51.100.53"),
            ("router", "192.0.2.1", "192.0.2.254"),
            ("classless_static_routes", ["198.51.100.0/24:192.0.2.1"]),
        ])
        with patch.object(ip_info, "sniff", return_value=[packet]), patch.object(ip_info, "sendp"):
            result = ip_info.get_dhcp_options(iface="test-interface")
        values = {number: value for number, _, value, _ in result}
        self.assertEqual(values[6], "192.0.2.53, 198.51.100.53")
        self.assertEqual(values[3], "192.0.2.1, 192.0.2.254")
        self.assertEqual(values[121], "198.51.100.0/24:192.0.2.1")


class PortSocketRegressionTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(port_scanner.socket, "gethostbyname", return_value="192.0.2.1")
        self.resolve = patcher.start()
        self.addCleanup(patcher.stop)

    def test_invalid_hostname_is_reported_before_any_socket_is_opened(self):
        self.resolve.side_effect = OSError("Name does not resolve")
        done = MagicMock()
        with patch.object(port_scanner.socket, "socket") as socket:
            with self.assertRaisesRegex(OSError, "does not resolve"):
                port_scanner.scan_ports("invalid.example", [80, 443], done_callback=done)
        socket.assert_not_called()
        done.assert_not_called()

    def test_socket_is_closed_when_connection_or_timeout_setup_fails(self):
        for method in ("connect_ex", "settimeout"):
            with self.subTest(method=method):
                socket = MagicMock()
                socket.__enter__.return_value = socket
                getattr(socket, method).side_effect = OSError("fixture failure")
                with patch.object(port_scanner.socket, "socket", return_value=socket):
                    self.assertEqual(port_scanner.scan_ports("192.0.2.1", [80]), [])
                socket.__exit__.assert_called_once()

    def test_open_port_results_and_progress_survive_socket_context(self):
        socket = MagicMock()
        socket.__enter__.return_value = socket
        socket.connect_ex.return_value = 0
        progress, done = MagicMock(), MagicMock()
        with patch.object(port_scanner.socket, "socket", return_value=socket):
            result = port_scanner.scan_ports("192.0.2.1", [443],
                                              progress_callback=progress,
                                              done_callback=done)
        self.assertEqual(result, [{"port": 443, "service": "HTTPS"}])
        progress.assert_called_once_with(1, 1)
        done.assert_called_once_with(result)
        self.resolve.assert_called_once_with("192.0.2.1")
        socket.connect_ex.assert_called_once_with(("192.0.2.1", 443))
        socket.__exit__.assert_called_once_with(None, None, None)


if __name__ == "__main__":
    unittest.main()
