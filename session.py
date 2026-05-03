from datetime import datetime


class SessionManager:
    """
    Holds all scan results captured during the current PiNT session.
    Results are accumulated in memory and can be exported at any time.
    """

    def __init__(self):
        self.port_scans  = []   # LLDP/CDP results
        self.ip_snapshots = []  # IP Info results
        self.mdns_scans  = []   # mDNS results
        self._listeners  = []   # UI callbacks to notify on change

    # ── Registration ─────────────────────────────────────────

    def register_listener(self, callback):
        """Register a function to call whenever the session changes."""
        self._listeners.append(callback)

    def _notify(self):
        for cb in self._listeners:
            try:
                cb()
            except Exception:
                pass

    # ── Adding results ────────────────────────────────────────

    def add_port_scan(self, device: dict):
        """Log an LLDP/CDP scan result."""
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "protocol":  device.get("protocol", "Unknown"),
            "switch":    device.get("name", "Unknown"),
            "port":      device.get("port", "Unknown"),
            "model":     device.get("description", device.get("model", "Unknown")),
            "ip":        device.get("ip", "Unknown"),
            "vlan":      device.get("vlan", "Unknown"),
        }
        self.port_scans.append(entry)
        self._notify()

    def add_ip_snapshot(self, ip_data: dict, dhcp_opts: list):
        """Log an IP Info scan result."""
        entry = {
            "timestamp":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "adapter":        ip_data.get("adapter", "Unknown"),
            "hostname":       ip_data.get("hostname", "Unknown"),
            "mac":            ip_data.get("mac", "Unknown"),
            "ip":             ip_data.get("ip", "Unknown"),
            "subnet":         ip_data.get("subnet", "Unknown"),
            "gateway":        ip_data.get("gateway", "Unknown"),
            "dns":            ", ".join(ip_data.get("dns", [])),
            "domain":         ip_data.get("domain", "Unknown"),
            "dhcp_enabled":   ip_data.get("dhcp_enabled", False),
            "dhcp_server":    ip_data.get("dhcp_server", "Unknown"),
            "lease_obtained": ip_data.get("lease_obtained", "Unknown"),
            "lease_expires":  ip_data.get("lease_expires", "Unknown"),
            "dhcp_options":   dhcp_opts,   # list of (num, label, value, flag)
        }
        self.ip_snapshots.append(entry)
        self._notify()

    def add_mdns_scan(self, devices: list):
        """Log an mDNS scan result (entire device list as one session entry)."""
        if not devices:
            return
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "devices":   list(devices),   # snapshot copy
        }
        self.mdns_scans.append(entry)
        self._notify()

    # ── Queries ───────────────────────────────────────────────

    def total_entries(self):
        return len(self.port_scans) + len(self.ip_snapshots) + len(self.mdns_scans)

    def has_data(self):
        return self.total_entries() > 0

    def clear(self):
        self.port_scans.clear()
        self.ip_snapshots.clear()
        self.mdns_scans.clear()
        self._notify()