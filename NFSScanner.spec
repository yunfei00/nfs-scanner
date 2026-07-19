# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Windows release packaging."""

from PyInstaller.utils.hooks import collect_submodules


datas = [
    ("README.md", "."),
    ("docs", "docs"),
    ("nfs_scanner/devices", "nfs_scanner/devices"),
    ("resources", "resources"),
]

hiddenimports = [*collect_submodules("nfs_scanner")]

a = Analysis(
    ["run.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name="NFSScanner",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="NFSScanner",
)
