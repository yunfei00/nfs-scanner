# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Windows release packaging."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

project_root = Path(__file__).resolve().parent

datas = [
    (str(project_root / "README.md"), "."),
    (str(project_root / "docs"), "docs"),
]

hiddenimports = [*collect_submodules("nfs_scanner")]

a = Analysis(
    [str(project_root / "run.py")],
    pathex=[str(project_root)],
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
