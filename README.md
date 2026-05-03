# 🍺 PiNT - Port Identifier Network Tool

![Version](https://img.shields.io/badge/version-v0.3.1-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Protocol](https://img.shields.io/badge/protocols-LLDP%20%7C%20CDP%20%7C%20mDNS-green)

A lightweight portable Windows tool that identifies which switch port your machine is connected to using LLDP and CDP network discovery protocols, and discovers mDNS/Bonjour devices on the local network. Built for field technicians who need quick port identification without complex network tools.

---

## 🚀 Features

- **Live LLDP & CDP capture** — detects both protocols simultaneously
- **Auto protocol detection** — works with Cisco (CDP) and all other vendors (LLDP)
- **Displays switch name, port, model, IP and VLAN**
- **mDNS / Bonjour browser** — discovers devices broadcasting on the local network
- **Simple / Full view toggle** — clean view for quick reference, full view for Bonjour gateway config
- **Active IP resolution** — sends mDNS queries to resolve device IPs
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
├── pint.py          # Main application & GUI
├── scanner.py       # Packet capture logic
├── lldp_parser.py   # LLDP protocol parser
├── cdp_parser.py    # CDP protocol parser
└── logo.png         # Application logo
```

---

## 🔖 Versions

| Version | Description |
|---------|-------------|
| v0.1 | Initial release — LLDP support |
| v0.2 | Added CDP support, refactored codebase |
| v0.3 | mDNS / Bonjour browser tab |
| v0.3.1 | Bug fixes, CSV export, IP resolve button |
| v0.3.2 | Planned — mDNS improvements, Windows IP resolution fixes |
| v0.4 | Planned — Export to XLS / CSV for report generation |
| v0.5 | Planned — Extended IP & DHCP information tab |
| v0.6 | Planned — Quick launch SSH / Telnet / HTTP(S) from management IP |
| v0.7 | Planned — macOS support |

---

## 🛠️ Built With

- Python
- Scapy
- Tkinter
- PyInstaller

---

## 📋 Roadmap

- [x] **v0.1** — LLDP support
- [x] **v0.2** — CDP support
- [x] **v0.3** — mDNS tab with Bonjour-style browser
- [x] **v0.3.1** — CSV export, IP resolve button, Simple/Full view toggle
- [ ] **v0.3.2** — mDNS improvements, Windows IP resolution fixes
- [ ] **v0.4** — Export results to XLS/CSV; session-scoped export for multi-port switch audits
- [ ] **v0.5** — Extended IP tab: DHCP server discovery, full IP/DNS/Gateway detail
- [ ] **v0.6** — Quick launch buttons (SSH / Telnet / HTTP / HTTPS) next to management IP
- [ ] **v0.7** — macOS support

---

*Built as a Python learning project — vibe coded with Claude* 🍺
