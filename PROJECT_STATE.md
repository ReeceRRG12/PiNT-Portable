# PiNT desktop refresh

## Current maintenance task — 10 October 2026

Requested outcome: pull the latest code, review it for bugs, and fix confirmed
defects. Fetched `origin`; `origin/main` and this clean worktree both started at
`45531cb`. Fast-forward integration reported already up to date.

Scope: bounded protocol, platform, GUI and export correctness review, with offline
regressions for confirmed defects. Retain the existing architecture and release
gates; no live network scans. On 10 October Reece authorized pushing these fixes
to main and publishing a new version. Release target: `v1.6.0-beta.2`, titled
PiNT Desktop 1.6 Beta 2, with Windows x64 and macOS arm64/x64 packages. Keep it
a prerelease until the existing hardware/signing gates are satisfied. Finish when the fixes pass
available tests and the remaining platform/hardware limits are recorded. Passing
checks provide evidence for this scope, not a guarantee that all bugs are absent.

## Checkpoint — maintenance review verified, 10 October 2026

- Source remains based on `45531cb3c7b9a8fe68197ed86e3c6136f1beb186`, matching
  freshly fetched `origin/main`. Changes are local and uncommitted on
  `codex/release-1.6-checkpoint`; nothing was pushed or published.
- Fixed SNMP OID decoding, truncated BER acceptance, and WALK subtree/progress
  checks; blank LLDP descriptions no longer abort discovery.
- DHCP capture starts before sending INFORM, matches transaction/client, and
  preserves multiple DNS/router addresses and classless routes.
- TCP hostname failures now report errors instead of zero open ports; sockets
  close on exceptions, controls recover, and results keep the scanned hostname.
- Monitor keeps the selected adapter instead of silently falling back to Wi-Fi;
  Change Adapter can return to Auto-detect. Unknown DHCP stays unknown in summaries.
- XLSX exports preserve discovered text as text (including leading `=` and Excel
  error-like strings) and remove XML-invalid control characters. mDNS CSV exports
  use UTF-8 and report file-write failures.
- Added 30 regression tests. Final command:
  `/tmp/pint-bugcheck-20261010/bin/python -m unittest discover -s tests -v`
  ran 70 tests: 69 passed, one Windows-only PowerShell parser check skipped on Mac.
  Protocol/export defects were reproduced against the original code before fixes.
- Runtime imports, byte compilation, Python 3.11 syntax compatibility, dependency
  consistency (`pip check`), and `git diff --check` passed. Tests ran in an isolated
  Python 3.14.4 environment installed from the existing requirements.
- Final suite uses mocked network I/O and explicit packet addresses. An earlier
  DHCP fixture attempted implicit ARP resolution and failed to open BPF in the
  sandbox; corrected before final verification, which emitted no capture warnings.
- No live-network acceptance, visual GUI validation, package rebuild, or Windows
  execution was performed in this task. Existing stable-release gates still apply.

## Release checkpoint — 1.6 Beta 2 published, 10 October 2026

- Reece explicitly authorized overriding the usage reserve to finish this release.
  The override applied to final verification/publication; normal reserve rules
  resume for subsequent work.
- Bugfix/version commit `c0711e02abf85131a2f21e4d1a7df69f00c33c43` was pushed
  to main without force and is the exact target of annotated tag `v1.6.0-beta.2`.
- [PiNT Desktop 1.6 Beta 2](https://github.com/ReeceRRG12/PiNT-Portable/releases/tag/v1.6.0-beta.2)
  was published on 10 October 2026 at 17:13 BST (16:13 UTC) as a prerelease.
  GitHub still identifies v1.5 as the latest stable release.
- Exact-commit CI passed:
  [Windows x64](https://github.com/ReeceRRG12/PiNT-Portable/actions/runs/38066471022),
  [macOS arm64/x64](https://github.com/ReeceRRG12/PiNT-Portable/actions/runs/38066470997).
  Workflows ran regression/import checks and packaged the app. Local suite:
  70 tests, 69 passed and one Windows-only check skipped on Mac.
- Windows executable verified: x64, fixed/product version 1.6.0.2,
  product string 1.6.0-beta.2 and prerelease flag. No embedded signature.
- Both Mac archives passed ZIP integrity checks and were extracted with ditto.
  Info.plists report version 1.6.0/build 1.6.2 and Beta 2. All 81 Mach-O files
  per package have the expected architecture (arm64 or x86_64). Both extracted
  apps passed `codesign --verify --deep --strict`. These remain ad-hoc signatures.
- Published assets: `PiNT-1.6-beta.2-windows-x64.exe`,
  `PiNT-1.6-beta.2-macos-arm64.zip`, `PiNT-1.6-beta.2-macos-x64.zip`, and
  `SHA256SUMS.txt`. All four remote upload sizes and SHA-256 digests matched the
  verified local files before and after publication; remote tag target verified.
- Local artifacts/manifests are in `/tmp/pint-release-beta2`; durable build evidence
  and downloads are the GitHub runs/release linked above. Committed release notes:
  `docs/release-notes-1.6-beta.2.md`.
- This final checkpoint is documentation after the release tag; it does not alter
  the released binaries. No live scans or physical-network acceptance were run.

Current stage: requested bugfix release complete. Next action before stable
promotion remains physical Windows/macOS network acceptance and Apple Developer
ID signing/notarization. Passing tests and builds do not guarantee zero bugs.

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
