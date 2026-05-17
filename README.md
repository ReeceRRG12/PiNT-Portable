# Pi Network Tools - PiNT Desktop 🍺 
(formally PiNT-Portable & Port Identifier) 

![Version](https://img.shields.io/badge/version-v1.3-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Protocol](https://img.shields.io/badge/protocols-LLDP%20%7C%20CDP%20%7C%20mDNS%20%7C%20ARP%20%7C%20SNMP-green)
[![Website](https://img.shields.io/badge/website-pinetworktools.com-blue)](https://pinetworktools.com)

A lightweight portable Windows tool for field technicians. Identifies which switch port your machine is connected to using LLDP and CDP, discovers mDNS/Bonjour devices, sweeps the local subnet with ARP, scans hosts for open ports, and queries SNMP-enabled devices. No complex network tools required.

---

## 🚀 Features

- **Live LLDP & CDP capture:** detects both protocols simultaneously
- **Auto protocol detection:** works with Cisco (CDP) and all other vendors (LLDP)
- **Multi-vendor LLDP support:** tested with TP-Link, Ruckus, UniFi and more
- **Port ID card layout:** Switch, Port, Protocol, Model, IP and VLAN displayed as live info cards
- **Network adapter picker:** detects all interfaces on launch, lets you choose the right one with a recommended highlight; remembers selection for the session
- **Quick Launch buttons:** once a management IP is found, one-click SSH and Telnet via PuTTY, or open HTTP/HTTPS in your browser
- **Port Monitor tab:** displays negotiated link speed and duplex; tracks dropped and errored packets since monitoring started for basic cable-test feedback
- **mDNS / Bonjour browser:** discovers devices broadcasting on the local network
- **Simple / Full view toggle:** clean view for quick reference, full view for Bonjour gateway config
- **Active IP resolution:** sends mDNS queries to resolve device IPs
- **Extended IP & DHCP tab:** full adapter detail including DHCP server, scope options and lease info
- **Colour-coded DHCP options:** flags standard, notable and unknown scope options at a glance
- **ARP Scanner:** sweeps the local subnet with ARP to discover all active devices; shows IP, MAC and hostname; auto-detects subnet from selected adapter
- **Port Scanner:** TCP connect-scan any host with presets (Top 20, Top 100, Web) or a custom port range; shows open ports with service name hints and a live progress bar
- **SNMP Query:** GET or WALK any SNMP v1/v2c device using a community string; includes common OID presets for system info, interfaces, ARP table, routing table and LLDP remote table; no external dependencies
- **Session-scoped export to XLS:** accumulate results across multiple scans and export as a single styled Excel file
- **Export to CSV:** save mDNS scan results for reporting
- **Copy to clipboard:** paste results directly into Teams or email
- **Scalable UI:** auto-detects screen resolution on startup and scales fonts, icons and layout accordingly; resizable window with 900x640 minimum
- **Auto-installs Npcap** if not already present
- **Single .exe:** no install required, just run it

---

## 📦 Download

Visit **[pinetworktools.com](https://pinetworktools.com)** for more info, screenshots and feature overview.

Head to the [Releases](../../releases) page and download the latest `pint.exe`

No Python required. Just download and run.

---

## ⚙️ Requirements

- Windows 10/11
- Admin rights (required for packet capture)
- Npcap (auto-installed on first run)
- A wired ethernet connection to a managed switch
- PuTTY (optional, required for SSH/Telnet quick launch buttons)

---

## 🗂️ Project Structure

```
PiNT-Portable/
├── pint.py               # Main application entry point & orchestrator
├── pint.spec             # PyInstaller build spec
├── session.py            # Session state manager (cross-cutting)
├── exporter.py           # XLS export logic (cross-cutting)
├── version_info.txt      # Windows EXE version metadata
├── requirements.txt
├── logo.png              # Taskbar / window icon
├── logo.ico
├── PiNT_InAppLogo.png    # Branded in-app sidebar logo
├── icons/                # Sidebar navigation icons (PNG, 24x24)
│   ├── PortID.png
│   ├── mDNS.png
│   ├── IP_Info.png
│   ├── Monitor.png
│   ├── Export.png
│   ├── settings.png
│   ├── About.png
│   ├── ARP.png
│   ├── PortScanner.png
│   └── SNMP.png
├── network/              # Network scanners, parsers and queries
│   ├── __init__.py
│   ├── scanner.py            # LLDP/CDP packet capture
│   ├── lldp_parser.py        # LLDP protocol parser
│   ├── cdp_parser.py         # CDP protocol parser
│   ├── mdns_scanner.py       # mDNS / Bonjour discovery & IP resolution
│   ├── arp_scanner.py        # ARP subnet sweep
│   ├── port_scanner.py       # TCP connect port scanner
│   ├── snmp_query.py         # SNMP v1/v2c GET & WALK (raw UDP, no dependencies)
│   └── ip_info.py            # IP & DHCP information gathering
└── gui/                  # GUI panels and shared widget helpers
    ├── __init__.py
    ├── theme.py              # Centralised colours, fonts and ttk dark styling
    ├── widgets.py            # Shared widget helpers (description, buttons, progress bar, results tree, copy)
    ├── scale_manager.py      # Screen resolution detection and CTk scaling
    ├── interface_picker.py   # Network adapter selection dialog
    ├── port_tab.py           # Port ID tab (LLDP/CDP + card grid + quick launch)
    ├── mdns_tab.py           # mDNS browser tab
    ├── ip_tab.py             # IP Info & DHCP tab
    ├── monitor_tab.py        # Port Monitor tab (link speed, packet drops)
    ├── arp_tab.py            # ARP Scanner tab
    ├── portscan_tab.py       # Port Scanner tab
    ├── snmp_tab.py           # SNMP Query tab
    ├── export_tab.py         # Session export tab
    └── settings_tab.py       # Settings panel
```

---

## 🔖 Versions

| Version | Description |
|---------|-------------|
| v0.1    | Initial release, LLDP support |
| v0.2    | Added CDP support, refactored codebase |
| v0.3    | mDNS / Bonjour browser tab |
| v0.3.1  | CSV export, IP resolve button, Simple/Full view toggle |
| v0.3.2  | Windows mDNS service discovery fix, About dialog |
| v0.4    | Extended IP & DHCP tab |
| v0.5    | Session-scoped export to XLS |
| v0.5.1  | Improved About dialog with clickable links |
| v0.5.2  | Multi-vendor LLDP parser rework (Ruckus, UniFi, TP-Link) |
| v0.5.3  | XLS column auto-fit, tab descriptions |
| v0.6    | GUI refactored into gui/ package; network adapter picker; quick launch SSH/Telnet/HTTP/HTTPS |
| v0.7    | Port Monitor tab: link speed/duplex, dropped packet counter; EXE publisher metadata; Change adapter button fix |
| v1.0    | Full GUI overhaul: sidebar navigation, branded in-app logo, progress bars on scans, Settings panel, About panel, larger window |
| v1.1    | CustomTkinter migration: resizable window, auto-scaling UI, dark themed components, Port ID card grid, polished monitor and about panels |
| v1.2    | ARP Scanner, Port Scanner and SNMP Query tabs; dependency-free SNMP v1/v2c engine; unified cyan icon tinting |
| **v1.3**| **Current** - Internal code refactor: centralised theme tokens, shared widget helpers in `gui/widgets.py`, scanners grouped into a `network/` package |
| Future  | Integrated iPerf3 tester |
| Future  | macOS support |

---

## 🛠️ Built With

- Python
- Scapy
- CustomTkinter
- Pillow
- openpyxl
- PyInstaller 

---

## 📋 Roadmap

- [x] **v0.1** - LLDP support
- [x] **v0.2** - CDP support
- [x] **v0.3** - mDNS tab with Bonjour-style browser
- [x] **v0.3.1** - CSV export, IP resolve button, Simple/Full view toggle
- [x] **v0.3.2** - Windows mDNS service discovery fix, About dialog
- [x] **v0.4** - Extended IP & DHCP tab with colour-coded scope options
- [x] **v0.5** - Session-scoped XLS export with Port Scans, IP Snapshots and mDNS sheets
- [x] **v0.5.1** - Improved About dialog with clickable email and GitHub links
- [x] **v0.5.2** - Multi-vendor LLDP parser rework with proper TLV parsing for Ruckus, UniFi, TP-Link and any IEEE 802.1AB compliant switch
- [x] **v0.5.3** - XLS column auto-fit, tab descriptions added for each tab
- [x] **v0.6** - GUI refactored into `gui/` package (one file per tab); network adapter picker on launch with recommended highlighting; quick launch buttons for SSH/Telnet (PuTTY) and HTTP/HTTPS once a management IP is detected
- [x] **v0.7** - Port Monitor tab: negotiated link speed and duplex, live dropped/errored packet counter (basic cable-test feedback); EXE publisher metadata (Pi Network Tools); Change adapter button now always shows the picker
- [x] **v1.0** - Full GUI overhaul: sidebar navigation replaces tab bar; branded in-app logo with aspect-ratio scaling; animated progress bars on Port ID and mDNS scans; Settings panel for scan timeouts and monitor poll interval; About panel inline; larger 1380x960 window
- [x] **v1.1** - CustomTkinter migration: auto-scaling UI based on screen resolution; resizable window (min 900x640); Port ID tab redesigned with live info card grid; dark-themed Treeview and scrollbars; centralised theme and scale manager modules; polished Monitor, About and sidebar panels throughout
- [x] **v1.2** - ARP Scanner tab (subnet sweep, IP/MAC/hostname); Port Scanner tab (TCP connect scan with Top 20/100/Web presets and custom range); SNMP Query tab (GET and WALK, v1/v2c, dependency-free raw UDP implementation); unified cyan icon tinting across all sidebar icons
- [x] **v1.3** - Internal code refactor for maintainability: every hardcoded colour pulled into `gui/theme.py`; new `gui/widgets.py` with shared helpers (`description`, `primary_button`, `secondary_button`, `scan_progressbar`, `results_tree`, `copy_to_clipboard`) collapsing ~280 lines of per-tab boilerplate; all 8 scanner/parser/query modules grouped into a `network/` package
- [ ] **Future** - Integrated iPerf3 tester
- [ ] **Future** - macOS support

---

## 📬 Contact

Got questions or feedback? Reach out at **reece@pinetworktools.com**

---

*Built as a Python learning project, vibe coded with Claude* 🍺


*Fully open source, built with ❤️ for the networking community*
