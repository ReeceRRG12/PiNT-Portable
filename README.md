# 🖧 PiNT - Port Identifier Network Tool
![Version](https://img.shields.io/badge/version-v0.2-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Protocol](https://img.shields.io/badge/protocols-LLDP%20%7C%20CDP-green)

A lightweight portable Windows tool that identifies which switch port your machine is connected to using LLDP and CDP network discovery protocols. Built for field technicians who need quick port identification without complex network tools.

---

## 🚀 Features

- **Live LLDP & CDP capture** — detects both protocols simultaneously
- **Auto protocol detection** — works with Cisco (CDP) and all other vendors (LLDP)
- **Displays switch name, port, model, IP and VLAN**
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
| v0.3 | Coming soon — mDNS / Bonjour browser tab |
| v0.4 | Planned — Extended IP & DHCP information tab |
| v0.5 | Planned — Export to XLS / CSV for report generation |
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

- [x] LLDP support
- [x] CDP support
- [ ] **v0.3** — mDNS tab with Bonjour-style browser showing friendly and raw service strings
- [ ] **v0.4** — Extended IP tab: DHCP server discovery (expandable), scope options, full IP/DNS/Gateway detail
- [ ] **v0.5** — Export results to XLS/CSV; session-scoped export for multi-port switch audits and report generation
- [ ] **v0.6** — Quick launch buttons (SSH / Telnet / HTTP / HTTPS) next to management IP, with live port status indicators
- [ ] **v0.7** — macOS support

---

*Built as a Python learning project — vibe coded with Claude* 🍺
