# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for FocusTimer — single-file Windows .exe
Usage:
    pyinstaller FocusTimer.spec
"""

import sys
from pathlib import Path

_root = Path(SPECPATH)

a = Analysis(
    [str(_root / 'main.py')],
    pathex=[str(_root)],
    binaries=[],
    datas=[
        (str(_root / 'assets' / 'icon.ico'), 'assets'),
        (str(_root / 'assets' / 'sounds'), 'assets/sounds'),
    ],
    hiddenimports=[
        'PyQt6',
        'pygame',
        'matplotlib',
        'numpy',
        'matplotlib.backends.backend_qtagg',
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
    name='FocusTimer',
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
    icon=str(_root / 'assets' / 'icon.ico'),
)
