# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for directory-based desktop release output."""

from __future__ import annotations

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

project_root = Path(__file__).resolve().parent

# Keep package data collection explicit and maintainable.
datas = collect_data_files("nfs_scanner", include_py_files=False)

# Ensure plugin-like modules and optional adapter paths are importable in frozen mode.
hiddenimports = [
    *collect_submodules("nfs_scanner.devices"),
    *collect_submodules("nfs_scanner.ui"),
    *collect_submodules("nfs_scanner.analysis"),
    *collect_submodules("nfs_scanner.storage"),
    *collect_submodules("nfs_scanner.scan"),
]


block_cipher = None


a = Analysis(
    ["run.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="NFSScanner",
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="NFSScanner",
)
