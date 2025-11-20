# -*- coding: utf-8 -*-
"""
測試智能戰鬥系統整合
"""

import sys
import os

# 添加路徑
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("🧪 測試智能戰鬥系統整合")
print("=" * 60)

# 測試 1: 檢查檔案
print("\n1️⃣ 檢查檔案...")
files_to_check = [
    "auto_combat_system.py",
    "adaptive_navigation_system.py",
    "smart_auto_combat.py"
]

for file in files_to_check:
    if os.path.exists(file):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} 不存在!")

# 測試 2: 嘗試導入
print("\n2️⃣ 測試導入...")
try:
    from auto_combat_system import SmartAutoCombatUI
    print("   ✅ 成功導入 SmartAutoCombatUI from auto_combat_system")
except Exception as e:
    print(f"   ❌ 導入失敗: {e}")

try:
    from adaptive_navigation_system import AdaptiveNavigationSystem
    print("   ✅ 成功導入 AdaptiveNavigationSystem")
except Exception as e:
    print(f"   ❌ 導入失敗: {e}")

# 測試 3: 檢查相依套件
print("\n3️⃣ 檢查相依套件...")
required_packages = [
    "ttkbootstrap",
    "cv2",
    "numpy",
    "pyautogui",
    "win32gui"
]

for package in required_packages:
    try:
        __import__(package if package != "cv2" else "cv2")
        print(f"   ✅ {package}")
    except ImportError:
        print(f"   ❌ {package} 未安裝")

# 測試 4: 嘗試創建獨立視窗 (不執行 mainloop)
print("\n4️⃣ 測試創建介面...")
try:
    from auto_combat_system import SmartAutoCombatUI
    import tkinter as tk
    
    # 創建測試視窗
    test_window = tk.Toplevel()
    test_window.withdraw()
    
    # 創建智能戰鬥介面
    app = SmartAutoCombatUI(parent_window=test_window)
    print("   ✅ 成功創建介面實例")
    
    # 檢查介面組件
    if hasattr(app, 'root'):
        print("   ✅ root 屬性存在")
    if hasattr(app, 'config'):
        print("   ✅ config 屬性存在")
    if hasattr(app, 'nav_system'):
        print("   ✅ nav_system 屬性存在")
    
    # 清理
    test_window.destroy()
    
except Exception as e:
    print(f"   ❌ 創建介面失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ 測試完成!")
print("=" * 60)
print("\n如果所有測試都通過,可以在主程式中使用智能戰鬥功能。")
print("在左側選單點擊「4.自動戰鬥」即可開啟。")
input("\n按 Enter 退出...")
