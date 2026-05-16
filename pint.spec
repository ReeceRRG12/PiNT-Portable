# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

ctk_datas = collect_data_files('customtkinter')

a = Analysis(
    ['pint.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('logo.png',           '.'),
        ('logo.ico',           '.'),
        ('PiNT_InAppLogo.png', '.'),
        ('gui',                'gui'),
        ('icons',              'icons'),
        *ctk_datas,
    ],
    hiddenimports=[
        'gui',
        'gui.interface_picker',
        'gui.port_tab',
        'gui.mdns_tab',
        'gui.ip_tab',
        'gui.export_tab',
        'gui.monitor_tab',
        'gui.settings_tab',
        'gui.arp_tab',
        'gui.portscan_tab',
        'gui.snmp_tab',
        'gui.scale_manager',
        'gui.theme',
        'arp_scanner',
        'port_scanner',
        'snmp_query',
        'customtkinter',
        'darkdetect',
        'packaging',
        'PIL',
        'PIL._tkinter_finder',
        'psutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='pint',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo.ico'],
    version='version_info.txt',
)
