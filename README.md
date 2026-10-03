# Pi Network Tools - PiNT Desktop 🍺  
(formally PiNT-Portable & Port Identifier) 

![Version](https://img.shields.io/badge/version-1.6%20Beta%201-orange)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey)
![Protocol](https://img.shields.io/badge/protocols-LLDP%20%7C%20CDP%20%7C%20mDNS%20%7C%20ARP%20%7C%20SNMP-green)
[![Website](https://img.shields.io/badge/website-pinetworktools.com-blue)](https://pinetworktools.com)

A lightweight desktop network tool for field technicians, with Windows executable and macOS app builds. Identifies which switch port your machine is connected to using LLDP and CDP, discovers mDNS/Bonjour devices, sweeps the local subnet with ARP, scans hosts for open ports, and queries SNMP-enabled devices. No complex network tools required.

---

## 🚀 Features

- **Live LLDP & CDP capture:** detects both protocols simultaneously
- **Auto protocol detection:** works with Cisco (CDP) and all other vendors (LLDP)
- **Multi-vendor LLDP support:** tested with TP-Link, Ruckus, UniFi and more
- **Port ID card layout:** Switch, Port, Protocol, Model, IP and VLAN displayed as live info cards
- **Network adapter picker:** detects all interfaces on launch, lets you choose the right one with a recommended highlight; remembers selection for the session
- **Quick Launch buttons:** once a management IP is found, SSH via macOS Terminal or Windows PuTTY/OpenSSH, optional Telnet clients, and HTTP/HTTPS in your browser
- **Port Monitor tab:** displays negotiated link speed and duplex; tracks dropped and errored packets since monitoring started for basic cable-test feedback
- **mDNS / Bonjour browser:** discovers devices broadcasting on the local network
- **Simple / Full view toggle:** clean view for quick reference, full view for Bonjour gateway config
- **mDNS address resolution:** prefers advertised SRV-target A/AAAA records, using the packet source as a fallback; proxy responses retain the service device address
- **Extended IP & DHCP tab:** full adapter detail including DHCP server, scope options and lease info
- **Colour-coded DHCP options:** flags standard, notable and unknown scope options at a glance
- **ARP Scanner:** sweeps the local subnet with ARP to discover all active devices; shows IP, MAC and hostname; auto-detects subnet from selected adapter; one-click XLSX export for loading into PiNT Live
- **Port Scanner:** TCP connect-scan any host with presets (Top 20, Top 100, Web) or a custom port range; shows open ports with service name hints and a live progress bar
- **SNMP Query:** GET or WALK any SNMP v1/v2c device using a community string; includes common OID presets for system info, interfaces, ARP table, routing table and LLDP remote table; no external dependencies
- **Session-scoped export to XLS:** accumulate results across multiple scans and export as a single styled Excel file
- **Export to CSV:** save mDNS scan results for reporting
- **Copy to clipboard:** paste results directly into Teams or email
- **Readable desktop UI:** grouped navigation, clear result cards, sortable tables, brighter labels, and window sizing that respects display height and native DPI
- **Capture setup guidance:** opens the official Npcap download page when needed on Windows
- **Saved preferences:** scan timeouts and monitor interval persist across launches
- **Desktop bundles:** Windows `.exe` and macOS `.app`; Python is included

---

## 📦 Download

Visit **[pinetworktools.com](https://pinetworktools.com)** for more info, screenshots and feature overview.

Download [PiNT Desktop 1.6 Beta 1](https://github.com/ReeceRRG12/PiNT-Portable/releases/tag/v1.6.0-beta.1):

- Windows x64: `PiNT-1.6-beta.1-windows-x64.exe`
- Mac with Apple Silicon: `PiNT-1.6-beta.1-macos-arm64.zip`
- Mac with Intel: `PiNT-1.6-beta.1-macos-x64.zip`

No Python installation is required. Extract the Mac ZIP to access `PiNT.app`.
Version 1.6 is a beta for testing; [v1.5 remains the stable release](https://github.com/ReeceRRG12/PiNT-Portable/releases/tag/v1.5).
The `stable` branch preserves the previous `main`; `main` contains the 1.6 update.

---

## ⚙️ Requirements and platform setup

- Windows 10/11, or macOS with a build matching Apple Silicon / Intel.
- Wired Ethernet connected to a managed switch for LLDP/CDP port identification.
- Packet capture access for Port ID, ARP, mDNS capture, and DHCP scope probing.
- SSH: macOS Terminal, or PuTTY/Windows OpenSSH. Telnet needs an optional client.

On **Windows**, install [Npcap](https://npcap.com/#download) with permissions
appropriate to your account. Administrator access is needed to install the driver;
capture privileges depend on its installation options.

On **macOS**, packet capture uses the system's BPF devices. Configure capture access
with an administrator-approved setup, such as the optional ChmodBPF package in the
[official Wireshark installer](https://www.wireshark.org/docs/wsug_html_chunked/ChBuildInstallOSXInstall.html).
PiNT does not change capture permissions. Ordinary TCP/SNMP queries and reading local
IP configuration do not require raw packet access. If access is missing, capture
panels report a setup error rather than a misleading empty result.

The Windows beta executable is unsigned. Mac beta builds are ad-hoc signed,
**not** Apple Developer ID signed or notarized, so operating-system security
warnings or launch restrictions may apply. CI builds Windows x64, Apple Silicon
and Intel packages and runs offline tests. Physical network capture acceptance
testing and Apple distribution signing/notarization remain outstanding before
promoting macOS support to a stable release.

## What's new in 1.6 Beta 1

- Fix CDP management IPv4 parsing, honor SNMP v1/v2c selection, and reject malformed OIDs.
- Resolve mDNS proxy records using the service target's advertised address.
- Read the selected adapter through Windows CIM or macOS SystemConfiguration;
  distinguish unavailable DHCP details from DHCP being disabled.
- Refresh shared typography, colors, navigation, connection cards, and sortable tables.
- Save timeouts and monitor settings in the user's PiNT configuration directory.
- Include `psutil` in clean installations, and run offline regressions before packaging.

### Run from source

Use Python 3.11 or later with Tk support. Create and activate a virtual environment
(`python3 -m venv .venv` on macOS, `py -3.11 -m venv .venv` on Windows), then run:

```sh
python -m pip install -r requirements.txt
python pint.py
```

Preferences are written only when Apply Settings is pressed, to
`~/Library/Application Support/PiNT/settings.json` on macOS or
`%APPDATA%/PiNT/settings.json` on Windows. Scan results remain session-only.

### Test and build

```sh
python -m unittest discover -s tests -v
```

Tests use packet fixtures and mocked sockets; they do not scan your network.

Build on the target operating system:

```sh
# Windows: dist/pint.exe
python -m PyInstaller --noconfirm pint.spec

# macOS: dist/PiNT.app (architecture follows the build Python)
python -m PyInstaller --noconfirm pint-macos.spec
codesign --verify --deep --strict dist/PiNT.app
```

If `codesign` reports Finder metadata in a synced workspace, stage the macOS build
outside it, for example with `--distpath /tmp/pint-dist --workpath /tmp/pint-build`,
and transfer the verified app as a ZIP preserving symlinks.

macOS builders can supply `PINT_CODESIGN_IDENTITY` for their Apple Developer ID;
notarization is a separate release step. Build jobs produce artifacts on pull
requests and pushes to main; these are not automatically published releases.
See [PROJECT_STATE.md](PROJECT_STATE.md) for this implementation's verified status
and remaining acceptance checks.

---

## 🗂️ Project Structure

```
PiNT-Portable/
├── pint.py               # Main application entry point & orchestrator
├── pint.spec             # Windows PyInstaller build spec
├── pint-macos.spec       # macOS app build spec
├── app_settings.py       # Persistent user preferences
├── tests/                # Offline regression tests
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
│   ├── mdns_scanner.py       # mDNS / Bonjour discovery; IPs read from packet source
│   ├── arp_scanner.py        # ARP subnet sweep
│   ├── port_scanner.py       # TCP connect port scanner
│   ├── snmp_query.py         # SNMP v1/v2c GET & WALK (raw UDP, no dependencies)
│   ├── platform_info.py      # Windows CIM / macOS SystemConfiguration
│   ├── capture.py            # Capture setup error messages
│   └── ip_info.py            # Selected-adapter IP & DHCP gathering
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
| v1.3    | Internal code refactor: centralised theme tokens, shared widget helpers in `gui/widgets.py`, scanners grouped into a `network/` package |
| v1.4    | ARP tab XLSX export for PiNT Live: flat IP / MAC / Hostname workbook in the schema PiNT Live's *Load ARP List…* sidebar consumes |
| **v1.5**| **Stable** - mDNS IP read directly from packet source address; removes active resolve step and Resolve IPs button; adds GitHub Actions Windows EXE build |
| **v1.6 Beta 1** | **Current beta** - refreshed desktop UI, native macOS packages for Apple Silicon and Intel, Windows adapter improvements, saved settings, and CDP/SNMP/mDNS fixes |
| Future  | Integrated iPerf3 tester |

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
- [x] **v1.4** - ARP tab gains a one-click XLSX export: flat single-sheet workbook with `IP Address`, `MAC Address` and `Hostname` columns, ready to drop into PiNT Live's *Load ARP List…* sidebar to enrich per-switch port documentation; default filename derived from the scanned subnet and date
- [x] **v1.5** - mDNS IP detection now passive: sender's unicast IP is read directly from the IP layer of each mDNS response packet (`pkt[IP].src`), removing the need for active queries, hostname resolution chains, or the separate Resolve IPs button; GitHub Actions workflow added for automated Windows EXE builds
- [ ] **Future** - Integrated iPerf3 tester
- [x] **v1.6 Beta 1** - refreshed desktop UI, native macOS packages, platform-aware adapter details, saved settings, and CDP/SNMP/mDNS fixes
- [ ] **Before macOS stable** - physical-network acceptance testing and Apple distribution signing/notarization

---

## 📬 Contact

Got questions or feedback? Reach out at **reece@pinetworktools.com**

---

*Built as a Python learning project, vibe coded with Claude* 🍺


*Fully open source, built with ❤️ for the networking community*
