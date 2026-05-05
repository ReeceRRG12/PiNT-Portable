# 🍺 PiNT - Port Identifier Network Tool
![Version](https://img.shields.io/badge/version-v1.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Protocol](https://img.shields.io/badge/protocols-LLDP%20%7C%20CDP%20%7C%20mDNS-green)

A lightweight portable Windows tool that identifies which switch port your machine is connected to using LLDP and CDP network discovery protocols, and discovers mDNS/Bonjour devices on the local network. Built for field technicians who need quick port identification without complex network tools.

---

## 🚀 Features

- **Live LLDP & CDP capture** — detects both protocols simultaneously
- **Auto protocol detection** — works with Cisco (CDP) and all other vendors (LLDP)
- **Multi-vendor LLDP support** — tested with TP-Link, Ruckus, UniFi and more
- **Displays switch name, port, model, IP and VLAN**
- **Network adapter picker** — detects all interfaces on launch, lets you choose the right one with a recommended highlight; remembers selection for the session
- **Quick Launch buttons** — once a management IP is found, one-click SSH and Telnet via PuTTY, or open HTTP/HTTPS in your browser
- **Port Monitor tab** — displays negotiated link speed and duplex; tracks dropped and errored packets since monitoring started for basic cable-test feedback
- **mDNS / Bonjour browser** — discovers devices broadcasting on the local network
- **Simple / Full view toggle** — clean view for quick reference, full view for Bonjour gateway config
- **Active IP resolution** — sends mDNS queries to resolve device IPs
- **Extended IP & DHCP tab** — full adapter detail including DHCP server, scope options and lease info
- **Colour-coded DHCP options** — flags standard, notable and unknown scope options at a glance
- **Session-scoped export to XLS** — accumulate results across multiple scans and export as a single styled Excel file
- **Export to CSV** — save mDNS scan results for reporting
- **Copy to clipboard** — paste results directly into Teams or email
- **Auto-installs Npcap** if not already present
- **Single .exe** — no install required, just run it
- **Dark theme GUI** with PiNT branding

---

## 📦 Download

Head to the [Releases](../../releases) page and download the latest `pint.exe`

No Python required. Just download and run.

---

## ⚙️ Requirements

- Windows 10/11
- Admin rights (required for packet capture)
- Npcap (auto-installed on first run)
- A wired ethernet connection to a managed switch
- PuTTY (optional — required for SSH/Telnet quick launch buttons)

---

## 🗂️ Project Structure

```
PiNT-Portable/
├── pint.py               # Main application entry point & orchestrator
├── scanner.py            # Packet capture logic (LLDP/CDP)
├── mdns_scanner.py       # mDNS discovery & IP resolution
├── lldp_parser.py        # LLDP protocol parser
├── cdp_parser.py         # CDP protocol parser
├── ip_info.py            # IP & DHCP information gathering
├── session.py            # Session state manager
├── exporter.py           # XLS export logic
├── logo.png              # Taskbar / window icon
├── PiNT_InAppLogo.png    # Branded in-app sidebar logo
├── icons/                # Sidebar navigation icons (PNG, 24x24)
│   ├── PortID.png
│   ├── mDNS.png
│   ├── IP_Info.png
│   ├── Monitor.png
│   ├── Export.png
│   ├── settings.png
│   └── About.png
└── gui/
    ├── __init__.py
    ├── interface_picker.py   # Network adapter selection dialog
    ├── port_tab.py           # Port ID tab (LLDP/CDP + quick launch)
    ├── mdns_tab.py           # mDNS browser tab
    ├── ip_tab.py             # IP Info & DHCP tab
    ├── monitor_tab.py        # Port Monitor tab (link speed, packet drops)
    ├── export_tab.py         # Session export tab
    └── settings_tab.py       # Settings panel
```

---

## 🔖 Versions

| Version | Description |
|---------|-------------|
| v0.1    | Initial release — LLDP support |
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
| **v1.0**| **Current** — Full GUI overhaul: sidebar navigation, branded in-app logo, progress bars on scans, Settings panel, About panel, larger window |
| Future  | Integrated iPerf3 tester |
| Future  | macOS support |

---

## 🛠️ Built With

- Python
- Scapy
- Tkinter
- openpyxl
- PyInstaller

---

## 📋 Roadmap

- [x] **v0.1** — LLDP support
- [x] **v0.2** — CDP support
- [x] **v0.3** — mDNS tab with Bonjour-style browser
- [x] **v0.3.1** — CSV export, IP resolve button, Simple/Full view toggle
- [x] **v0.3.2** — Windows mDNS service discovery fix, About dialog
- [x] **v0.4** — Extended IP & DHCP tab with colour-coded scope options
- [x] **v0.5** — Session-scoped XLS export with Port Scans, IP Snapshots and mDNS sheets
- [x] **v0.5.1** — Improved About dialog with clickable email and GitHub links
- [x] **v0.5.2** — Multi-vendor LLDP parser rework — proper TLV parsing for Ruckus, UniFi, TP-Link and any IEEE 802.1AB compliant switch
- [x] **v0.5.3** — XLS column auto-fit, tab descriptions added for each tab
- [x] **v0.6** — GUI refactored into `gui/` package (one file per tab); network adapter picker on launch with recommended highlighting; quick launch buttons for SSH/Telnet (PuTTY) and HTTP/HTTPS once a management IP is detected
- [x] **v0.7** — Port Monitor tab: negotiated link speed and duplex, live dropped/errored packet counter (basic cable-test feedback); EXE publisher metadata (Pi Network Tools); Change adapter button now always shows the picker
- [x] **v1.0** — Full GUI overhaul: sidebar navigation replaces tab bar; branded in-app logo with aspect-ratio scaling; animated progress bars on Port ID and mDNS scans; Settings panel for scan timeouts and monitor poll interval; About panel inline; larger 1380×960 window
- [ ] **Future** — Integrated iPerf3 tester
- [ ] **Future** — macOS support

---

## 📬 Contact

Got questions or feedback? Reach out at **reece@pinetworktools.com**

---

*Built as a Python learning project — vibe coded with Claude* 🍺

*Fully open source — built with ❤️ for the networking community*
