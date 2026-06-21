# -*- mode: python ; coding: utf-8 -*-
import sys

a = Analysis(
    ['src/simple_to_pdf/cli/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('settings.json', '.'),
        ('pyproject.toml', '.'),
        ('LICENSE', '.'),
        ('THIRD-PARTY-NOTICES.txt', '.'),
        ('lang', 'lang'),
        ('icons', 'icons'),
    ],
    hiddenimports=['PIL._tkinter_finder', 'customtkinter'],
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
    name='Simple_to_PDF',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'] if sys.platform == 'win32' else [],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Simple_to_PDF',
)