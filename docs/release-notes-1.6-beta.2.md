# PiNT Desktop 1.6 Beta 2

Bugfix update to 1.6 Beta 1 for Windows and macOS.

## Fixes

- Correct SNMP OID decoding and WALK subtree boundaries; stop backwards/repeated replies and reject truncated responses.
- Handle empty LLDP descriptions without aborting switch discovery.
- Start DHCP capture before sending INFORM, match replies to the transaction and client, and preserve multiple DNS/router addresses and classless routes.
- Keep Port Monitor on the selected adapter, allow returning to Auto-detect, and distinguish unknown DHCP status from static configuration.
- Report TCP hostname-resolution failures, restore controls after scan errors, close sockets on failures, and retain the scanned hostname in results and clipboard output.
- Export discovered values as literal spreadsheet text and remove unsupported control characters; write mDNS CSV as UTF-8 and report save failures.

## Downloads

- Windows x64: `PiNT-1.6-beta.2-windows-x64.exe`
- macOS Apple Silicon: `PiNT-1.6-beta.2-macos-arm64.zip`
- macOS Intel: `PiNT-1.6-beta.2-macos-x64.zip`
- `SHA256SUMS.txt`: checksums for all three packages.

Extract the Mac ZIP to access `PiNT.app`. No Python installation is required.

## Verification and beta limitations

Includes 30 new offline regression tests. The suite contains 70 tests; the Windows-only PowerShell parser check is skipped on macOS. Network tests use fixtures and mocked I/O.

This remains a prerelease; v1.5 remains the stable release. Physical-network acceptance is still required. Windows capture requires Npcap; macOS capture requires suitable BPF access. The Windows executable is unsigned. Mac packages are ad-hoc signed, not Apple Developer ID signed or notarized, so operating-system warnings or launch restrictions may apply.

Full changes: https://github.com/ReeceRRG12/PiNT-Portable/compare/v1.6.0-beta.1...v1.6.0-beta.2
