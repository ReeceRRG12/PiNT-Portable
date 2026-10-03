import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app_settings import AppSettings
from gui.desktop import launch_terminal, management_address
from network.scanner import scan
from network.arp_scanner import scan_arp


class SettingsTests(unittest.TestCase):
    def test_preferences_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "PiNT" / "settings.json"
            settings = AppSettings(path)
            settings.port_timeout = 45
            settings.monitor_poll_ms = 5000
            settings.save()
            restored = AppSettings(path)
            self.assertEqual(restored.port_timeout, 45)
            self.assertEqual(restored.monitor_poll_ms, 5000)

    def test_corrupt_and_invalid_preferences_use_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            for contents in ("broken", "[]", json.dumps({"port_timeout": -1,
                                                        "mdns_timeout": "oops"})):
                path.write_text(contents)
                settings = AppSettings(path)
                self.assertEqual(settings.port_timeout, 30)
                self.assertEqual(settings.mdns_timeout, 30)


class TerminalTests(unittest.TestCase):
    def test_discovery_cannot_inject_terminal_arguments(self):
        for value in ("-oProxyCommand=bad", "192.0.2.1; echo bad", "$(bad)", "fe80::1%x;bad"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                management_address(value)

    @patch("gui.desktop.subprocess.run")
    @patch("gui.desktop.sys.platform", "darwin")
    def test_mac_ssh_uses_terminal_registered_url(self, run):
        launch_terminal("ssh", "2001:db8::1")
        self.assertEqual(run.call_args.args[0],
                         ["/usr/bin/open", "-a", "Terminal", "ssh://[2001:db8::1]"])

    @patch("gui.desktop.subprocess.Popen")
    @patch("gui.desktop._find_putty", return_value="putty.exe")
    @patch("gui.desktop.sys.platform", "win32")
    def test_windows_keeps_putty_support(self, find, popen):
        launch_terminal("ssh", "192.0.2.1")
        popen.assert_called_once_with(["putty.exe", "-ssh", "192.0.2.1"])


class AdapterAndExportTests(unittest.TestCase):
    def test_picker_keeps_unassigned_link_but_orders_active_ip_first(self):
        from gui.interface_picker import _enumerate_interfaces
        interfaces = {
            name: SimpleNamespace(ip=ip, mac="00:11:22:33:44:55", description=name)
            for name, ip in [("en1", "0.0.0.0"), ("en2", "192.0.2.2"), ("en3", "")]
        }
        stats = {name: SimpleNamespace(isup=name != "en3") for name in interfaces}
        with patch("scapy.all.conf", SimpleNamespace(ifaces=interfaces)), patch(
                "psutil.net_if_stats", return_value=stats), patch("gui.interface_picker.sys.platform", "darwin"), patch(
                "network.platform_info.macos_interface_details", return_value={}):
            found = _enumerate_interfaces()
        self.assertEqual([row["name"] for row in found], ["en2", "en1"])
        self.assertEqual(found[1]["ip"], "No IPv4 address")
        self.assertFalse(found[0]["recommended"])

    def test_unknown_dhcp_is_preserved_in_export(self):
        from exporter import _build_ip_sheet
        from session import SessionManager
        from openpyxl import Workbook
        session = SessionManager()
        session.add_ip_snapshot({}, [])
        workbook = Workbook()
        _build_ip_sheet(workbook, session.ip_snapshots)
        self.assertEqual(workbook["IP Snapshots"]["J2"].value, "Unavailable")


class CaptureTests(unittest.TestCase):
    @patch("network.scanner.sniff", side_effect=PermissionError("BPF denied"))
    def test_port_capture_failure_does_not_report_no_switch(self, sniff):
        success, failure = Mock(), Mock()
        scan(success, iface="en9", error_callback=failure)
        success.assert_not_called()
        failure.assert_called_once()
        self.assertIn("capture", failure.call_args.args[0].lower())

    @patch("network.arp_scanner.srp", side_effect=PermissionError("capture denied"))
    def test_arp_capture_failure_does_not_report_zero_devices(self, srp):
        success, failure = Mock(), Mock()
        scan_arp("192.0.2.0/30", iface="en9", callback=success, error_callback=failure)
        success.assert_not_called()
        failure.assert_called_once()

    @patch("network.scanner.parse_lldp", return_value={"protocol": "LLDP", "port": "7"})
    @patch("network.scanner.sniff")
    def test_port_capture_stops_and_returns_once(self, sniff, parse):
        packet = bytes.fromhex("0180c200000e00112233445588cc")
        def receive(**kwargs):
            self.assertEqual(kwargs["iface"], "en9")
            self.assertFalse(kwargs["stop_filter"](packet))
            kwargs["prn"](packet)
            self.assertTrue(kwargs["stop_filter"](packet))
        sniff.side_effect = receive
        done = Mock()
        scan(done, iface="en9")
        done.assert_called_once_with({"protocol": "LLDP", "port": "7"})


if __name__ == "__main__":
    unittest.main()
