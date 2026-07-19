# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Windows release packaging."""

from pathlib import Path

from nfs_scanner.version import APP_NAME, APP_VERSION


version_parts = [int(part) for part in APP_VERSION.split(".")]
version_tuple = tuple((version_parts + [0, 0, 0, 0])[:4])
version_info_path = Path("build") / "windows_version_info.txt"
version_info_path.parent.mkdir(parents=True, exist_ok=True)
version_info_path.write_text(
    f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple},
    prodvers={version_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'080404B0',
        [StringStruct(u'CompanyName', u'{APP_NAME}'),
         StringStruct(u'FileDescription', u'Near Field Scan System'),
         StringStruct(u'FileVersion', u'{APP_VERSION}'),
         StringStruct(u'InternalName', u'NFSScanner'),
         StringStruct(u'LegalCopyright', u'Copyright (c) 2026. All rights reserved.'),
         StringStruct(u'OriginalFilename', u'NFSScanner.exe'),
         StringStruct(u'ProductName', u'{APP_NAME}'),
         StringStruct(u'ProductVersion', u'{APP_VERSION}')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)
""",
    encoding="utf-8",
)

datas = [
    ("README.md", "."),
    ("LICENSE", "."),
    ("THIRD_PARTY_NOTICES.md", "."),
    ("docs/USER_GUIDE.md", "docs"),
    ("docs/hardware_acceptance_matrix.md", "docs"),
    ("config/devices.example.yaml", "config"),
    ("config/scan_defaults.yaml", "config"),
    ("resources", "resources"),
]

hiddenimports = []

a = Analysis(
    ["run.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "pyqtgraph", "pytest", "ruff", "tkinter"],
    noarchive=False,
    optimize=1,
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
    version=str(version_info_path),
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
