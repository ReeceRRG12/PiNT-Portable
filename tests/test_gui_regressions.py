"""Exercise UI callbacks without creating windows or sending network traffic."""

import socket
import csv
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import psutil

from gui.export_tab import ExportTab
from gui.monitor_tab import _find_psutil_iface
from gui.mdns_tab import MdnsTab
from gui.portscan_tab import PortScanTab
from pint import PiNTApp
from session import SessionManager


class MonitorAdapterTests(unittest.TestCase):
    def _find(self, selected, scapy, addresses):
        with patch("scapy.all.conf", SimpleNamespace(ifaces=scapy)), patch(
                "psutil.net_if_addrs", return_value=addresses), patch(
                "psutil.net_if_stats", return_value={
                    name: SimpleNamespace(isup=True) for name in addresses}):
            return _find_psutil_iface(selected)

    def test_selected_unassigned_adapter_is_matched_by_name(self):
        addresses = {"en0": [SimpleNamespace(family=socket.AF_INET, address="192.0.2.1")],
                     "en9": []}
        self.assertEqual(self._find("en9", {}, addresses), "en9")

    def test_selected_missing_adapter_does_not_fall_back_to_wifi(self):
        addresses = {"Wi-Fi": [SimpleNamespace(family=socket.AF_INET, address="192.0.2.1")]}
        selected = SimpleNamespace(ip="0.0.0.0", mac="00:11:22:33:44:55")
        self.assertIsNone(self._find("missing", {"missing": selected}, addresses))

    def test_windows_unassigned_adapter_matches_mac_with_different_separators(self):
        addresses = {"Wi-Fi": [SimpleNamespace(family=socket.AF_INET, address="192.0.2.1")],
                     "Ethernet": [SimpleNamespace(family=psutil.AF_LINK, address="00-11-22-33-44-55")]}
        selected = SimpleNamespace(ip="0.0.0.0", mac="00:11:22:33:44:55")
        self.assertEqual(self._find("npcap-guid", {"npcap-guid": selected}, addresses), "Ethernet")

    def test_ambiguous_ip_does_not_select_an_arbitrary_adapter(self):
        addresses = {name: [SimpleNamespace(family=socket.AF_INET, address="192.0.2.1")]
                     for name in ("Ethernet", "Wi-Fi")}
        selected = SimpleNamespace(ip="192.0.2.1", mac="")
        self.assertIsNone(self._find("npcap-guid", {"npcap-guid": selected}, addresses))

    def test_auto_detect_still_selects_active_ipv4_adapter(self):
        addresses = {"lo0": [SimpleNamespace(family=socket.AF_INET, address="127.0.0.1")],
                     "en0": [SimpleNamespace(family=socket.AF_INET, address="192.0.2.1")]}
        self.assertEqual(self._find(None, {}, addresses), "en0")


class PortScanCallbackTests(unittest.TestCase):
    def _tab(self):
        tab = PortScanTab.__new__(PortScanTab)
        for name in ("_root", "_status", "_scan_btn", "_copy_btn", "_detail", "_tree"):
            setattr(tab, name, Mock())
        tab._tree.get_children.return_value = []
        tab._root.after.side_effect = lambda delay, callback, *args: callback(*args)
        tab._progress = {}
        tab._host_var = Mock(get=Mock(return_value="192.0.2.10"))
        tab._preset_var = Mock(get=Mock(return_value="Web"))
        tab._timeout_var = Mock(get=Mock(return_value="1"))
        return tab

    @patch("gui.portscan_tab.widgets.copy_to_clipboard")
    @patch("gui.portscan_tab.threading.Thread")
    def test_result_and_copy_keep_original_host_after_user_edits_input(self, thread, copy):
        tab = self._tab()
        tab._start_scan()
        tab._host_var.get.return_value = "192.0.2.99"
        tab._update_ui([{"port": 443, "service": "HTTPS"}])
        self.assertIn("192.0.2.10", tab._status.configure.call_args.kwargs["text"])
        tab._copy()
        self.assertIn("192.0.2.10", copy.call_args.args[1])
        self.assertNotIn("192.0.2.99", copy.call_args.args[1])
        self.assertEqual(thread.call_args.kwargs["args"][0], "192.0.2.10")

    @patch("network.port_scanner.scan_ports", side_effect=OSError("resolver failed"))
    def test_worker_failure_restores_scan_button_and_displays_error(self, scan):
        tab = self._tab()
        tab._run_scan("192.0.2.10", [80], 1)
        tab._scan_btn.configure.assert_called_with(state="normal")
        tab._detail.configure.assert_called_with(text="resolver failed")
        self.assertIn("failed", tab._status.configure.call_args.kwargs["text"])


class AppCallbackTests(unittest.TestCase):
    @patch("pint.get_iface_display", return_value="Auto-detect")
    @patch("pint.InterfacePicker", return_value=SimpleNamespace(result=None))
    def test_change_interface_can_return_to_auto_detect(self, picker, display):
        app = PiNTApp.__new__(PiNTApp)
        app.root = Mock()
        app._state = SimpleNamespace(selected_iface="en9")
        app._iface_label = Mock()
        app._change_interface()
        self.assertIsNone(app._state.selected_iface)
        app._iface_label.configure.assert_called_once_with(text="Auto-detect")

    def test_session_summary_distinguishes_unknown_dhcp_from_static(self):
        session = SessionManager()
        session.add_ip_snapshot({"ip": "192.0.2.10"}, [])
        session.add_ip_snapshot({"ip": "192.0.2.11", "dhcp_enabled": False}, [])
        session.add_ip_snapshot({"ip": "192.0.2.12", "dhcp_enabled": True,
                                 "dhcp_server": "192.0.2.1"}, [])
        tab = ExportTab.__new__(ExportTab)
        tab._state = SimpleNamespace(session=session)
        tab._tree = Mock()
        tab._tree.get_children.return_value = []
        tab._status = Mock()
        tab._export_btn = Mock()
        tab.refresh()
        summaries = [call.kwargs["values"][2] for call in tab._tree.insert.call_args_list]
        self.assertEqual(summaries, ["192.0.2.10 (DHCP status unavailable)",
                                    "192.0.2.11 (static)",
                                    "192.0.2.12 via 192.0.2.1"])


class MdnsExportTests(unittest.TestCase):
    def _tab(self):
        tab = MdnsTab.__new__(MdnsTab)
        tab._results = [{"friendly": "打印机 — Café", "type": "Printer",
                         "ip": "192.0.2.1", "raw": "打印机._ipp._tcp.local"}]
        tab.status = Mock()
        return tab

    def test_csv_export_preserves_unicode_with_explicit_utf8(self):
        tab = self._tab()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "discovery.csv"
            with patch("gui.mdns_tab.filedialog.asksaveasfilename", return_value=str(path)), patch(
                    "gui.mdns_tab.open", wraps=open) as output:
                tab._export_csv()
            self.assertEqual(output.call_args.kwargs["encoding"], "utf-8")
            with path.open(encoding="utf-8", newline="") as saved:
                rows = list(csv.reader(saved))
        self.assertEqual(rows[1], ["打印机 — Café", "Printer", "192.0.2.1",
                                   "打印机._ipp._tcp.local"])
        self.assertIn("Exported", tab.status.configure.call_args.kwargs["text"])

    @patch("gui.mdns_tab.filedialog.asksaveasfilename", return_value="unwritable.csv")
    @patch("gui.mdns_tab.open", side_effect=PermissionError("Permission denied"))
    def test_csv_save_failure_is_reported_without_escaping_callback(self, output, dialog):
        tab = self._tab()
        tab._export_csv()
        self.assertEqual(tab.status.configure.call_args.kwargs["text"],
                         "Export failed: Permission denied")


if __name__ == "__main__":
    unittest.main()
