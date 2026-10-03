"""Read the selected adapter's configuration without sending network traffic.

Windows uses CIM JSON; macOS uses the public SystemConfiguration framework.
Unavailable DHCP metadata remains unknown, never an inferred "disabled" state.
"""
import ctypes
from datetime import datetime, timezone
import ipaddress
import json
import plistlib
import re
import socket
import subprocess
import sys


def empty_config():
    return dict(adapter="Unknown", ip="Unknown", subnet="Unknown",
                gateway="Unknown", dns=[], dhcp_server="Unknown",
                dhcp_enabled=None, lease_obtained="Unavailable",
                lease_expires="Unavailable", mac="Unknown",
                hostname=socket.gethostname(), domain="Unknown")


def _list(value):
    return value if isinstance(value, list) else ([] if value is None else [value])


def _ipv4(value):
    try:
        return ipaddress.ip_address(value).version == 4
    except (ValueError, TypeError):
        return False


def _mac(value):
    return re.sub(r"[^0-9a-f]", "", str(value).lower())


def _identity(value):
    # Scapy/Npcap names contain the CIM SettingID in braces.
    text = str(value or "")
    match = re.search(r"\{([^}]+)\}", text)
    return (match.group(1) if match else text).casefold()


WINDOWS_QUERY = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
Get-CimInstance -ClassName Win32_NetworkAdapterConfiguration |
Where-Object { $_.IPEnabled } |
Select-Object Description, SettingID, IPAddress, IPSubnet, DefaultIPGateway,
    DNSServerSearchOrder, DNSDomain, DHCPEnabled, DHCPServer, MACAddress,
    @{n='DHCPLeaseObtained';e={if ($_.DHCPLeaseObtained) {$_.DHCPLeaseObtained.ToString('o')}}},
    @{n='DHCPLeaseExpires';e={if ($_.DHCPLeaseExpires) {$_.DHCPLeaseExpires.ToString('o')}}} |
ConvertTo-Json -Depth 4 -Compress
"""


def parse_windows_config(raw, iface, iface_ip=None, iface_mac=None):
    records = _list(json.loads(raw.lstrip("\ufeff")) if raw.strip() else None)
    matches = [r for r in records if _identity(r.get("SettingID")) == _identity(iface)
               or str(r.get("Description", "")).casefold() == str(iface).casefold()]
    # A known GUID must never silently fall back to another adapter.
    if not matches and not re.search(r"\{[^}]+\}", str(iface)):
        matches = [r for r in records
                   if (iface_ip and iface_ip in _list(r.get("IPAddress")))
                   or (iface_mac and _mac(iface_mac) == _mac(r.get("MACAddress")))]
    if len(matches) != 1:
        raise ValueError("The selected adapter could not be matched uniquely to Windows IP configuration.")
    row = matches[0]
    result = empty_config()
    addresses = _list(row.get("IPAddress"))
    index = next((i for i, address in enumerate(addresses) if _ipv4(address)), None)
    if index is None:
        raise ValueError("The selected adapter has no IPv4 configuration.")
    masks = _list(row.get("IPSubnet"))
    result.update(adapter=row.get("Description") or str(iface), ip=addresses[index],
                  subnet=masks[index] if index < len(masks) else "Unknown",
                  gateway=next((ip for ip in _list(row.get("DefaultIPGateway")) if _ipv4(ip)), "Unavailable"),
                  dns=_list(row.get("DNSServerSearchOrder")),
                  domain=row.get("DNSDomain") or "Unavailable",
                  mac=row.get("MACAddress") or iface_mac or "Unknown",
                  dhcp_enabled=row.get("DHCPEnabled"),
                  dhcp_server=row.get("DHCPServer") or "Unavailable",
                  lease_obtained=row.get("DHCPLeaseObtained") or "Unavailable",
                  lease_expires=row.get("DHCPLeaseExpires") or "Unavailable")
    return result


class _MacStore:
    """Small read-only CF bridge; all Copy/Create results are released."""

    def __init__(self):
        self.cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        self.sc = ctypes.CDLL("/System/Library/Frameworks/SystemConfiguration.framework/SystemConfiguration")
        pointer = ctypes.c_void_p
        signatures = [
            (self.cf, "CFStringCreateWithCString", [pointer, ctypes.c_char_p, ctypes.c_uint32], pointer),
            (self.cf, "CFPropertyListCreateData", [pointer, pointer, ctypes.c_long, ctypes.c_ulong, pointer], pointer),
            (self.cf, "CFDataGetLength", [pointer], ctypes.c_long),
            (self.cf, "CFDataGetBytePtr", [pointer], pointer),
            (self.cf, "CFRelease", [pointer], None),
            (self.sc, "SCDynamicStoreCopyValue", [pointer, pointer], pointer),
            (self.sc, "SCDynamicStoreCopyKeyList", [pointer, pointer], pointer),
            (self.sc, "SCDynamicStoreCopyDHCPInfo", [pointer, pointer], pointer),
            (self.sc, "DHCPInfoGetOptionData", [pointer, ctypes.c_uint8], pointer),
            (self.sc, "DHCPInfoGetLeaseStartTime", [pointer], pointer),
            (self.sc, "DHCPInfoGetLeaseExpirationTime", [pointer], pointer),
        ]
        for library, name, args, result in signatures:
            function = getattr(library, name)
            function.argtypes, function.restype = args, result

    def _decode(self, value):
        if not value:
            return None
        data = self.cf.CFPropertyListCreateData(None, value, 200, 0, None)
        if not data:
            raise RuntimeError("macOS returned unreadable network configuration.")
        try:
            return plistlib.loads(ctypes.string_at(self.cf.CFDataGetBytePtr(data),
                                                  self.cf.CFDataGetLength(data)))
        finally:
            self.cf.CFRelease(data)

    def _copy(self, function, key):
        name = self.cf.CFStringCreateWithCString(None, key.encode("utf-8"), 0x08000100)
        if not name:
            raise RuntimeError("Could not encode the macOS network service name.")
        try:
            return function(None, name)
        finally:
            self.cf.CFRelease(name)

    def _read(self, function, key):
        value = self._copy(function, key)
        try:
            return self._decode(value)
        finally:
            if value:
                self.cf.CFRelease(value)

    def get(self, key):
        return self._read(self.sc.SCDynamicStoreCopyValue, key) or {}

    def keys(self, pattern):
        return self._read(self.sc.SCDynamicStoreCopyKeyList, pattern) or []

    def dhcp(self, service):
        info = self._copy(self.sc.SCDynamicStoreCopyDHCPInfo, service)
        if not info:
            return {}
        try:
            # Get functions return borrowed objects; only release the info owner.
            start = self._decode(self.sc.DHCPInfoGetLeaseStartTime(info))
            expiry = self._decode(self.sc.DHCPInfoGetLeaseExpirationTime(info))
            server = self._decode(self.sc.DHCPInfoGetOptionData(info, 54))
            return dict(lease_obtained=_date(start),
                        lease_expires=_date(expiry) if expiry else ("Infinite" if start else "Unavailable"),
                        dhcp_server=socket.inet_ntoa(server) if server and len(server) == 4 else "Unavailable")
        finally:
            self.cf.CFRelease(info)


def _date(value):
    if isinstance(value, datetime):
        # plist dates use UTC, even when plistlib returns a naive datetime.
        return value.replace(tzinfo=timezone.utc).astimezone().isoformat(timespec="seconds")
    return "Unavailable"


def macos_interface_details(store=None):
    """Friendly service labels and hardware types keyed by BSD interface name.

    Setup records also cover disconnected adapters without an IPv4 lease.
    AirPort is normally the Hardware field even though Type is Ethernet.
    Failure leaves the caller free to display the original Scapy information.
    """
    if store is None and sys.platform != "darwin":
        return {}
    try:
        store = store or _MacStore()
        details = {}
        for key in sorted(store.keys(r"Setup:/Network/Service/.*/Interface")):
            interface = store.get(key)
            device = interface.get("DeviceName")
            if not device:
                continue
            hardware = str(interface.get("Hardware", "")).casefold()
            subtype = str(interface.get("SubType", "")).casefold()
            kind = str(interface.get("Type", "")).casefold()
            if hardware in ("airport", "wifi", "wi-fi") or subtype == "airport":
                itype = "Wireless"
            elif (device.startswith(("bridge", "utun", "tun", "tap", "vlan", "bond"))
                  or hardware in ("bridge", "vlan", "bond", "bluetooth")
                  or kind in ("ppp", "ipsec", "6to4", "vpn")):
                itype = "Virtual/VPN"
            elif hardware == "ethernet" or kind == "ethernet":
                itype = "Wired"
            else:
                itype = "Network"
            service = store.get(key.rsplit("/", 1)[0])
            details.setdefault(device, {
                "description": service.get("UserDefinedName") or device,
                "type": itype,
            })
        return details
    except Exception:
        return {}


def read_macos_config(iface, iface_mac=None, store=None):
    store = store or _MacStore()
    matches = []
    for key in store.keys(r"State:/Network/Service/.*/IPv4"):
        state = store.get(key)
        if state.get("InterfaceName") == str(iface):
            matches.append((key.split("/")[-2], state))
    if len(matches) != 1:
        raise ValueError("The selected adapter has no unique active macOS IPv4 service.")
    service, state = matches[0]
    setup = store.get(f"Setup:/Network/Service/{service}/IPv4")
    label = store.get(f"Setup:/Network/Service/{service}").get("UserDefinedName", iface)
    dns = store.get(f"State:/Network/Service/{service}/DNS")
    configured_dns = store.get(f"Setup:/Network/Service/{service}/DNS")
    # Per-service manually configured DNS takes precedence over DHCP values.
    dns.update(configured_dns)
    addresses, masks = state.get("Addresses", []), state.get("SubnetMasks", [])
    index = next((i for i, address in enumerate(addresses) if _ipv4(address)), None)
    if index is None:
        raise ValueError("The selected adapter has no IPv4 address.")
    method = setup.get("ConfigMethod")
    enabled = True if method == "DHCP" else (False if method in ("Manual", "INFORM", "LinkLocal", "PPP", "BOOTP") else None)
    result = empty_config()
    result.update(adapter=f"{label} ({iface})", ip=addresses[index],
                  subnet=masks[index] if index < len(masks) else "Unknown",
                  gateway=state.get("Router") or "Unavailable",
                  dns=dns.get("ServerAddresses", []),
                  domain=dns.get("DomainName") or "Unavailable",
                  mac=iface_mac or "Unknown", dhcp_enabled=enabled)
    if enabled:
        result.update(store.dhcp(service))
    if enabled is None:
        result["warning"] = "IP information loaded; DHCP configuration is unavailable for this adapter."
    return result


def get_platform_ip_config(iface, iface_ip=None, iface_mac=None):
    result = empty_config()
    try:
        if not iface:
            raise ValueError("Choose a network adapter before loading IP information.")
        if sys.platform == "win32":
            raw = subprocess.check_output(
                ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", WINDOWS_QUERY],
                encoding="utf-8", errors="replace", timeout=15,
                creationflags=0x08000000, stderr=subprocess.PIPE)
            return parse_windows_config(raw, iface, iface_ip, iface_mac)
        if sys.platform == "darwin":
            return read_macos_config(iface, iface_mac)
        raise RuntimeError("IP configuration is currently supported on Windows and macOS.")
    except Exception as exc:
        result["adapter"] = str(iface or "Unknown")
        result["error"] = f"Could not read the selected adapter: {exc}"
        return result
