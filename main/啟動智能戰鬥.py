# -*- coding: utf-8 -*-
"""
ChroLens 智能自動戰鬥 - 快速啟動
"""

import sys
import os

# 添加路徑
sys.path.insert(0, os.path.dirname(__file__))

try:
    from smart_auto_combat import SmartAutoCombatUI
    
    print("=" * 60)
    print("🎮 ChroLens 智能自動戰鬥系統")
    print("=" * 60)
    print()
    print("功能特色:")
    print("  ✅ 自適應地圖學習")
    print("  ✅ 自動敵人偵測與攻擊")
    print("  ✅ 智能移動與探索")
    print("  ✅ 卡住自動脫困")
    print("  ✅ 血量自動補給")
    print("  ✅ 即時統計追蹤")
    print()
    print("正在啟動介面...")
    print()
    
    app = SmartAutoCombatUI()
    app.run()

except ImportError as e:
    print(f"❌ 缺少必要模組: {e}")
    print()
    print("請安裝以下套件:")
    print("  pip install ttkbootstrap opencv-python pyautogui pywin32")
    input("\n按 Enter 退出...")

except Exception as e:
    print(f"❌ 啟動失敗: {e}")
    import traceback
    traceback.print_exc()
    input("\n按 Enter 退出...")
