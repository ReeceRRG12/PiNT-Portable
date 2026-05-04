# 🍺 PiNT - Port Identifier Network Tool
![Version](https://img.shields.io/badge/version-v0.5.2-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Protocol](https://img.shields.io/badge/protocols-LLDP%20%7C%20CDP%20%7C%20mDNS-green)

A lightweight portable Windows tool that identifies which switch port your machine is connected to using LLDP and CDP network discovery protocols, and discovers mDNS/Bonjour devices on the local network. Built for field technicians who need quick port identification without complex network tools.

---

## 🚀 Features

- **Live LLDP & CDP capture** — detects both protocols simultaneously
- **Auto protocol detection** — works with Cisco (CDP) and all other vendors (LLDP)
- **Multi-vendor LLDP support** — tested with TP-Link, Ruckus, UniFi and more
- **Displays switch name, port, model, IP and VLAN**
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

---

## 🗂️ Project Structure

```
PiNT-Portable/
├── pint.py           # Main application & GUI
├── scanner.py        # Packet capture logic (LLDP/CDP)
├── mdns_scanner.py   # mDNS discovery & IP resolution
├── lldp_parser.py    # LLDP protocol parser
├── cdp_parser.py     # CDP protocol parser
├── ip_info.py        # IP & DHCP information gathering
├── session.py        # Session state manager
├── exporter.py       # XLS export logic
└── logo.png          # Application logo
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
| **v0.5.2**  | **Current** — Multi-vendor LLDP parser rework (Ruckus, UniFi, TP-Link) |
| v0.5.3  | Planned — Report template fixes |
| v0.5.4  | Planned — UI update — descriptions added for each tab |
| v0.5.5  | Planned — Code refactor — each UI tab split into its own .py file |
| v0.6    | Planned — Quick launch SSH / Telnet / HTTP(S) from management IP |
| v0.7    | Planned — Integrated iPerf3 tester |
| v0.8    | Planned — macOS support |

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
- [ ] **v0.5.3** — Report template fixes
- [ ] **v0.5.4** — UI update with descriptions for each tab
- [ ] **v0.5.5** — Code refactor — each UI tab split into its own .py file for easier collaboration
- [ ] **v0.6** — Quick launch buttons (SSH / Telnet / HTTP / HTTPS) next to management IP
- [ ] **v0.7** — Integrated iPerf3 tester — run throughput, jitter and packet loss tests from within PiNT
- [ ] **v0.8** — macOS support

---

## 📬 Contact

Got questions or feedback? Reach out at **reece@pinetworktools.com**

---

*Built as a Python learning project — vibe coded with Claude* 🍺

*Fully open source — built with ❤️ for the networking community*
