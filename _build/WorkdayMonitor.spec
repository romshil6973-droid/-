# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for WorkdayMonitor
# Run: pyinstaller _build/WorkdayMonitor.spec

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Include CustomTkinter themes and assets
datas = collect_data_files('customtkinter')

a = Analysis(
    ['../main.py'],
    pathex=[os.path.abspath('..')],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'customtkinter',
        'PIL', 'PIL._tkinter_finder', 'PIL.Image',
        'win32api', 'win32con', 'win32gui',
        'psutil',
        'openpyxl', 'openpyxl.styles', 'openpyxl.utils',
        'sqlite3',
        'core.database', 'core.tracker', 'core.monitor',
        'core.reporter',
        'ui.app_window', 'ui.workday_tab', 'ui.achievements_tab',
        'ui.settings_tab', 'ui.theme',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WorkdayMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # No CMD window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../assets/icon.ico' if os.path.exists('../assets/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WorkdayMonitor',
)
