# PyInstaller spec file for Power BI Theme Creator
# Build with: pyinstaller build_exe.spec

import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Collect all PySide6 data files and modules
pyside6_data = collect_data_files('PySide6')
pyside6_binaries = []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=pyside6_binaries,
    datas=pyside6_data + [
        ('pbitheme', 'pbitheme'),
    ],
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtSvgWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
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
    name='PowerBI_Theme_Creator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='pbitheme/gui/app.ico' if __import__('os').path.exists('pbitheme/gui/app.ico') else None,
)
