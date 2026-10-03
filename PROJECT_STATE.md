# PiNT desktop refresh

## Brief

Purpose: make PiNT a more reliable, readable desktop network utility on Windows
and macOS while retaining its Python, Scapy, and CustomTkinter foundation.

Scope (3 October 2026): implement the reviewed correctness fixes, refresh the GUI,
and add macOS platform support and packaging, based on upstream commit `a430f27`.
Release decision: preserve that previous `main` on `stable`, merge the refresh to
`main`, and publish version 1.6 Beta 1 with tag `v1.6.0-beta.1` and Windows x64,
macOS Apple Silicon, and macOS Intel downloads.

Deliverables and success criteria:
- Offline regressions cover CDP addresses, SNMP version/input handling, mDNS
  proxy addresses, and selection of the correct network adapter.
- Readable, consistent GUI with window sizing suitable for laptop displays.
- Platform-aware IP information, terminal launch, icons, and capture errors.
- Windows executable and macOS app build definitions, with truthful setup and
  verification documentation.
- A tagged GitHub prerelease whose three downloadable packages are built from
  the tagged main commit; v1.5 remains the latest stable release.

Non-goals: toolkit rewrite, new scanning protocols, unified scan history,
changing host capture privileges, or installing drivers.

Constraints: protect unrelated work; do not run active network scans during
development; no claims of Windows/hardware verification without that testing.
Apple distribution signing/notarization and target-hardware capture validation
are gates for a stable macOS release. The explicitly authorized beta may ship
before these gates with the limitations disclosed.

Stages: (1) protocol and platform correctness; (2) GUI integration;
(3) offline tests, local Mac GUI/build checks and documentation;
(4) preserve stable, merge versioned source, verify main CI, tag and publish beta.

Finish condition: scoped implementation passes available checks and the tagged
beta is published with all three verified packages and documented limitations.

## Checkpoint — 1.6 Beta 1 published

- Base: `a430f27`, matching `origin/main` when pulled. Review branch:
  `codex/desktop-refresh-macos`, merged pull request #3. Refresh commit: `6a5c154`.
- Previous main is preserved on `stable` at `a430f273a73c408325765502463e1d285d470da9`.
  Main received the refresh and version metadata in merge commit
  `71c8b34600af70e2cb382347293b4ed4cf235162`, tagged `v1.6.0-beta.1`.
- [PiNT Desktop 1.6 Beta 1](https://github.com/ReeceRRG12/PiNT-Portable/releases/tag/v1.6.0-beta.1)
  was published on 3 October 2026 as a prerelease. GitHub still reports v1.5 as
  the latest stable release.
- Final main CI passed: [Windows x64](https://github.com/ReeceRRG12/PiNT-Portable/actions/runs/37157663206)
  and [macOS Apple Silicon/Intel](https://github.com/ReeceRRG12/PiNT-Portable/actions/runs/37157663210).
  Each download was built from the tagged merge commit.
- Published assets: `PiNT-1.6-beta.1-windows-x64.exe`,
  `PiNT-1.6-beta.1-macos-arm64.zip`, `PiNT-1.6-beta.1-macos-x64.zip`, and
  `SHA256SUMS.txt`. All four upload sizes and SHA-256 digests matched locally
  verified files. Windows x64 architecture, 1.6.0.1 fixed version, 1.6.0-beta.1
  product version and prerelease flag were verified; it is unsigned.
- Both Mac archives were extracted and verified: expected arm64/x86_64
  architecture, version 1.6.0 / build 1.6.1, beta label, and valid ad-hoc signature.
- Plain text website update: [docs/website-update-1.6-beta.1.txt](docs/website-update-1.6-beta.1.txt).
- Fixed CDP address parsing, SNMP version and invalid OID handling, proxy mDNS
  addresses, missing psutil, and selected-adapter IP/DHCP consistency.
- Added native Windows CIM and macOS SystemConfiguration readers, friendly Mac
  interface names, native terminal launching, and explicit capture errors.
- Refreshed palette, typography, navigation, connection cards and sortable tables;
  fixed sizing/DPI behavior and persisted scan preferences. Windows capture setup
  now links to official Npcap downloads rather than running a pinned installer.
- Offline verification: `python -m unittest discover -s tests -v` ran 40 tests:
  39 passed; one Windows-only PowerShell parser test was skipped on macOS.
- Mac native IP reader verified outside the sandbox: selected interface/address
  matched, DHCP metadata available, DNS entries returned. No DHCP/network probes.
- All ten panels opened at 1240x820 without callback errors. Isolated layout checks
  at 1000x640 and 1100x700 found no clipped visible controls or callback errors;
  DPI bounds checked at 1x, 1.5x and 2x. Custom scan-option states still need manual
  acceptance testing with realistic long data.
- Built native Apple Silicon app using Python 3.14.4, CustomTkinter 6.0.0,
  Scapy 2.8.0, and PyInstaller 6.22.3. App and adapter chooser were visually
  verified after extracting the final ZIP. No scans were started.
- Earlier local validation artifact: `dist/PiNT-macos-arm64.zip` (about 22 MB).
  The published beta downloads above supersede this local build. Verified with
  `codesign --verify --deep --strict` after extraction. This is ad-hoc local
  signing, not Developer ID signing/notarization.
- Build staging outside the Documents directory avoided Finder metadata that
  caused signature verification of an unpacked copy there to fail. The ZIP
  preserves the verified app; generated bundles are excluded from source control.
- Desktop validation must target exact PiNT bundle paths and task-owned
  process/session IDs, leaving other Python applications untouched.
- `git diff --check` passed. Capture, socket and terminal-launch tests used mocks;
  no live scans, privilege changes or driver installations were performed.

## Next action — stable release acceptance

The requested beta publication is complete. The release/tag and Actions records
linked above are the publication and build evidence. The checkpoint and website
copy are documentation added after the release tag; they do not change the apps.

Before promoting macOS support to stable: validate LLDP/CDP, ARP, mDNS, DHCP,
SNMP v1/v2c and SSH on physical target hardware, confirm capture setup on clean
systems, and complete Apple Developer ID signing/notarization. The Windows beta
is unsigned; macOS beta bundles use ad-hoc signing.

Parked enhancements: system/light theme, unified history/export for all tools,
and scan cancellation. These are not part of this completed implementation.
