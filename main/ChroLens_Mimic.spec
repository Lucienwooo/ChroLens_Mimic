# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Lucien\\Documents\\GitHub\\ChroLens_Mimic\\main\\ChroLens_Mimic.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Lucien\\Documents\\GitHub\\ChroLens_Mimic\\pic\\umi_奶茶色.ico', '.')],
    hiddenimports=[],
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
    name='ChroLens_Mimic',
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
    version='C:\\Users\\Lucien\\Documents\\GitHub\\ChroLens_Mimic\\main\\version_info.txt',
    icon=['C:\\Users\\Lucien\\Documents\\GitHub\\ChroLens_Mimic\\pic\\umi_奶茶色.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ChroLens_Mimic',
)
