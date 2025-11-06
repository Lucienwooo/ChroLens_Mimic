# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Lucien\\Documents\\GitHub\\ChroLens_Mimic\\main\\ChroLens_Mimic.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Lucien\\Documents\\GitHub\\ChroLens_Mimic\\main\\TTF', 'TTF'), ('C:\\Users\\Lucien\\Documents\\GitHub\\ChroLens_Mimic\\main\\update_system.py', '.')],
    hiddenimports=['pyautogui', 'pynput', 'keyboard', 'mouse', 'PIL', 'win32gui', 'win32con', 'win32api', 'ttkbootstrap', 'update_system'],
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
    icon=['C:\\Users\\Lucien\\Documents\\GitHub\\ChroLens_Mimic\\umi_奶茶色.ico'],
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
