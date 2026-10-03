"""Offline configuration fixtures: no capture or network requests."""
import copy
import base64
import json
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from network import platform_info as platform


WIFI_GUID = "{11111111-1111-1111-1111-111111111111}"
WIRED_GUID = "{22222222-2222-2222-2222-222222222222}"
WINDOWS_ADAPTERS = [
    {"Description": "Wi-Fi", "SettingID": WIFI_GUID,
     "IPAddress": ["192.0.2.2"], "IPSubnet": ["255.255.255.0"],
     "DefaultIPGateway": ["192.0.2.1"], "DHCPEnabled": True},
    {"Description": "Éthernet USB", "SettingID": WIRED_GUID,
     "IPAddress": ["2001:db8::2", "198.51.100.2"],
     "IPSubnet": ["64", "255.255.255.0"],
     "DefaultIPGateway": ["fe80::1", "198.51.100.1"],
     "DNSServerSearchOrder": ["198.51.100.53", "2001:db8::53"],
     "DNSDomain": "field.example", "MACAddress": "00:11:22:33:44:55",
     "DHCPEnabled": True, "DHCPServer": "198.51.100.1",
     "DHCPLeaseObtained": "2026-10-03T09:00:00+01:00",
     "DHCPLeaseExpires": "2026-10-04T09:00:00+01:00"},
]


class FakeMacStore:
    """Representative dictionaries returned by SystemConfiguration."""
    def __init__(self, method="DHCP"):
        self.values = {
            "State:/Network/Service/wifi/IPv4": {
                "InterfaceName": "en0", "Addresses": ["192.0.2.2"],
                "SubnetMasks": ["255.255.255.0"], "Router": "192.0.2.1"},
            "State:/Network/Service/wired/IPv4": {
                "InterfaceName": "en7", "Addresses": ["198.51.100.2"],
                "SubnetMasks": ["255.255.255.0"], "Router": "198.51.100.1"},
            "Setup:/Network/Service/wired": {"UserDefinedName": "USB Ethernet"},
            "Setup:/Network/Service/wired/IPv4": {"ConfigMethod": method},
            "State:/Network/Service/wired/DNS": {
                "ServerAddresses": ["198.51.100.53"], "DomainName": "field.example"},
        }
        self.dhcp_calls = []

    def keys(self, pattern):
        return [key for key in self.values if key.startswith("State:") and key.endswith("IPv4")]

    def get(self, key):
        return copy.deepcopy(self.values.get(key, {}))

    def dhcp(self, service):
        self.dhcp_calls.append(service)
        return dict(dhcp_server="198.51.100.1", lease_obtained="2026-10-03T08:00:00+00:00",
                    lease_expires="2026-10-04T08:00:00+00:00")


class WindowsConfigTests(unittest.TestCase):
    def test_selected_npcap_guid_wins_over_first_gateway(self):
        result = platform.parse_windows_config(json.dumps(WINDOWS_ADAPTERS),
                                               "\\Device\\NPF_" + WIRED_GUID)
        self.assertEqual(result["adapter"], "Éthernet USB")
        self.assertEqual(result["ip"], "198.51.100.2")
        self.assertEqual(result["subnet"], "255.255.255.0")
        self.assertEqual(result["gateway"], "198.51.100.1")
        self.assertEqual(result["dns"], ["198.51.100.53", "2001:db8::53"])
        self.assertTrue(result["dhcp_enabled"])
        self.assertEqual(result["lease_expires"], "2026-10-04T09:00:00+01:00")

    def test_single_adapter_json_object_and_static_ip(self):
        row = dict(WINDOWS_ADAPTERS[1], DHCPEnabled=False, DHCPLeaseObtained=None)
        result = platform.parse_windows_config("\ufeff" + json.dumps(row), WIRED_GUID)
        self.assertIs(result["dhcp_enabled"], False)
        self.assertEqual(result["lease_obtained"], "Unavailable")

    def test_unknown_guid_never_falls_back_to_another_adapter(self):
        with self.assertRaisesRegex(ValueError, "matched uniquely"):
            platform.parse_windows_config(json.dumps(WINDOWS_ADAPTERS), "{wrong-guid}", "192.0.2.2")

    def test_friendly_name_can_match_using_known_scapy_mac(self):
        result = platform.parse_windows_config(json.dumps(WINDOWS_ADAPTERS),
                                               "Ethernet", iface_mac="00-11-22-33-44-55")
        self.assertEqual(result["ip"], "198.51.100.2")

    def test_absent_dhcp_field_is_unknown(self):
        row = dict(WINDOWS_ADAPTERS[0])
        del row["DHCPEnabled"]
        self.assertIsNone(platform.parse_windows_config(json.dumps(row), WIFI_GUID)["dhcp_enabled"])

    def test_windows_command_is_bounded_and_structured(self):
        with patch.object(platform.sys, "platform", "win32"), patch.object(
                platform.subprocess, "check_output", return_value=json.dumps(WINDOWS_ADAPTERS)) as run:
            result = platform.get_platform_ip_config(WIRED_GUID)
        self.assertNotIn("error", result)
        self.assertEqual(run.call_args.kwargs["timeout"], 15)
        self.assertIn("ConvertTo-Json", run.call_args.args[0][-1])

    @unittest.skipUnless(sys.platform == "win32", "PowerShell parser requires Windows")
    def test_exact_windows_query_parses_in_powershell(self):
        encoded = base64.b64encode(platform.WINDOWS_QUERY.encode()).decode("ascii")
        script = ("$ErrorActionPreference='Stop'; [scriptblock]::Create("
                  "[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('"
                  + encoded + "'))) | Out-Null")
        subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                       check=True, timeout=15, capture_output=True)


class MacConfigTests(unittest.TestCase):
    def test_friendly_interface_names_and_hardware_types_without_ipv4(self):
        values = {
            "Setup:/Network/Service/wifi/Interface": {
                "DeviceName": "en0", "Type": "Ethernet", "Hardware": "AirPort"},
            "Setup:/Network/Service/wifi": {"UserDefinedName": "Wi-Fi"},
            "Setup:/Network/Service/usb/Interface": {
                "DeviceName": "en17", "Type": "Ethernet", "Hardware": "Ethernet"},
            "Setup:/Network/Service/usb": {"UserDefinedName": "USB 10/100/1000 LAN"},
            "Setup:/Network/Service/bridge/Interface": {
                "DeviceName": "bridge0", "Type": "Ethernet", "Hardware": "Ethernet"},
            "Setup:/Network/Service/bridge": {"UserDefinedName": "Thunderbolt Bridge"},
        }
        store = Mock()
        store.keys.return_value = [key for key in values if key.endswith("/Interface")]
        store.get.side_effect = lambda key: values.get(key, {})
        result = platform.macos_interface_details(store)
        self.assertEqual(result["en0"], {"description": "Wi-Fi", "type": "Wireless"})
        self.assertEqual(result["en17"], {"description": "USB 10/100/1000 LAN", "type": "Wired"})
        self.assertEqual(result["bridge0"]["type"], "Virtual/VPN")

    def test_interface_details_unavailable_falls_back_without_error(self):
        store = Mock()
        store.keys.side_effect = OSError("SystemConfiguration unavailable")
        self.assertEqual(platform.macos_interface_details(store), {})

    def test_selected_service_with_dhcp_metadata(self):
        store = FakeMacStore()
        result = platform.read_macos_config("en7", "00:11:22:33:44:55", store)
        self.assertEqual(result["adapter"], "USB Ethernet (en7)")
        self.assertEqual(result["ip"], "198.51.100.2")
        self.assertEqual(result["dns"], ["198.51.100.53"])
        self.assertEqual(result["dhcp_server"], "198.51.100.1")
        self.assertEqual(store.dhcp_calls, ["wired"])

    def test_static_service_does_not_read_dhcp_lease(self):
        store = FakeMacStore("Manual")
        result = platform.read_macos_config("en7", store=store)
        self.assertIs(result["dhcp_enabled"], False)
        self.assertEqual(store.dhcp_calls, [])

    def test_unknown_method_remains_unknown_and_warns(self):
        result = platform.read_macos_config("en7", store=FakeMacStore(None))
        self.assertIsNone(result["dhcp_enabled"])
        self.assertIn("unavailable", result["warning"])

    def test_manual_dns_overrides_only_this_services_dhcp_dns(self):
        store = FakeMacStore()
        store.values["Setup:/Network/Service/wired/DNS"] = {"ServerAddresses": ["203.0.113.53"]}
        result = platform.read_macos_config("en7", store=store)
        self.assertEqual(result["dns"], ["203.0.113.53"])
        self.assertEqual(result["domain"], "field.example")

    def test_disconnected_adapter_does_not_fall_back_to_wifi(self):
        with self.assertRaisesRegex(ValueError, "no unique active"):
            platform.read_macos_config("en9", store=FakeMacStore())

    def test_macos_failure_is_not_reported_as_dhcp_disabled(self):
        with patch.object(platform.sys, "platform", "darwin"), patch.object(
                platform, "read_macos_config", side_effect=OSError("access denied")):
            result = platform.get_platform_ip_config("en7")
        self.assertIsNone(result["dhcp_enabled"])
        self.assertIn("access denied", result["error"])


class IpTabTests(unittest.TestCase):
    def test_read_error_reenables_scan_without_success_or_export(self):
        from gui.ip_tab import IpTab
        tab = IpTab.__new__(IpTab)
        tab.status, tab.scan_btn = Mock(), Mock()
        tab._inner, tab._state = Mock(), SimpleNamespace(session=Mock())
        tab._update_ui({"error": "Selected adapter unavailable"}, [])
        self.assertEqual(tab.status.configure.call_args.kwargs["text"], "Selected adapter unavailable")
        tab.scan_btn.configure.assert_called_once_with(state="normal")
        tab._state.session.add_ip_snapshot.assert_not_called()

    def test_worker_uses_captured_adapter_for_both_reads(self):
        from gui.ip_tab import IpTab
        tab = IpTab.__new__(IpTab)
        tab._root = Mock()
        tab._state = SimpleNamespace(selected_iface="different-adapter-now")
        with patch("network.ip_info.get_ip_config", return_value={"dhcp_enabled": True}) as config, patch(
                "network.ip_info.get_dhcp_options", return_value=[]) as dhcp:
            tab._run_scan("captured-adapter")
        config.assert_called_once_with("captured-adapter")
        dhcp.assert_called_once_with(timeout=10, iface="captured-adapter")

    def test_auto_selection_uses_same_resolved_adapter_for_dhcp(self):
        from gui.ip_tab import IpTab
        tab = IpTab.__new__(IpTab)
        tab._root = Mock()
        with patch("network.ip_info.get_ip_config", return_value={
                "dhcp_enabled": True, "interface": "en7"}), patch(
                "network.ip_info.get_dhcp_options", return_value=[]) as dhcp:
            tab._run_scan(None)
        dhcp.assert_called_once_with(timeout=10, iface="en7")


if __name__ == "__main__":
    unittest.main()
