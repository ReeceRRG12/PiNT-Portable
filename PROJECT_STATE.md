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

## Checkpoint — implementation verified, beta release preparation

- Base: `a430f27`, matching `origin/main` when pulled. Review branch:
  `codex/desktop-refresh-macos`, pull request #3. Refresh commit: `6a5c154`.
- GitHub CI passed on the refresh commit: Windows x64 run `37157038514`,
  macOS Apple Silicon and Intel run `37157038551`. Version 1.6 Beta 1 metadata
  will be rebuilt and verified on the final main commit before publication.
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
- Deliverable: `dist/PiNT-macos-arm64.zip` (about 22 MB). Verified with
  `codesign --verify --deep --strict` after extraction. This is ad-hoc local
  signing, not Developer ID signing/notarization.
- Build staging outside the Documents directory avoided Finder metadata that
  caused signature verification of an unpacked copy there to fail. The ZIP
  preserves the verified app; generated bundles are excluded from source control.
- Desktop validation must target exact PiNT bundle paths and task-owned
  process/session IDs, leaving other Python applications untouched.
- `git diff --check` passed. Capture, socket and terminal-launch tests used mocks;
  no live scans, privilege changes or driver installations were performed.

## Next release action

Preserve `a430f273a73c408325765502463e1d285d470da9` as `stable`; merge the versioned
refresh to `main`; verify all three main CI packages, tag `v1.6.0-beta.1`, and
publish them in a GitHub prerelease. Validate published asset names and hashes.
Use GitHub release/tag and Actions records as the publication evidence.

Before promoting macOS support to stable: validate LLDP/CDP, ARP, mDNS, DHCP,
SNMP v1/v2c and SSH on physical target hardware, confirm capture setup on clean
systems, and complete Apple Developer ID signing/notarization. The Windows beta
is unsigned; macOS beta bundles use ad-hoc signing.

Parked enhancements: system/light theme, unified history/export for all tools,
and scan cancellation. These are not part of this completed implementation.
