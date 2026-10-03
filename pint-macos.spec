# Build on macOS: pyinstaller --noconfirm pint-macos.spec
# A native app for the build machine's architecture. Distribution signing and
# notarization require a separately configured Apple Developer identity.
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

a = Analysis(
    ['pint.py'],
    pathex=[], binaries=[],
    datas=[('logo.png', '.'), ('PiNT_InAppLogo.png', '.'), ('icons', 'icons'),
           *collect_data_files('customtkinter')],
    hiddenimports=[*collect_submodules('gui'), *collect_submodules('network'),
                   'PIL._tkinter_finder', 'psutil'],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name='PiNT',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, argv_emulation=False, target_arch=None,
    codesign_identity=os.environ.get('PINT_CODESIGN_IDENTITY'),
    entitlements_file=None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='PiNT')
app = BUNDLE(
    coll, name='PiNT.app', icon='logo.png', bundle_identifier='com.pinetworktools.pint',
    info_plist={
        'CFBundleDisplayName': 'PiNT',
        'CFBundleShortVersionString': '1.6.0',
        'CFBundleVersion': '1.6.1',
        'CFBundleGetInfoString': 'PiNT Desktop 1.6 Beta 1',
        'NSHighResolutionCapable': True,
        'NSLocalNetworkUsageDescription':
            'PiNT discovers switches and devices on the network you select.',
    },
)
