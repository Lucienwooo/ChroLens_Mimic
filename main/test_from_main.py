# -*- coding: utf-8 -*-
"""
測試從主程式啟動智能戰鬥
"""

import sys
import os

# 添加路徑
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("🧪 測試從主程式啟動智能戰鬥")
print("=" * 60)

try:
    import ttkbootstrap as tb
    from auto_combat_system import SmartAutoCombatUI
    
    print("\n✅ 成功導入必要模組")
    
    # 創建模擬主視窗
    print("\n📝 創建模擬主視窗...")
    root = tb.Window(title="ChroLens Mimic (測試)", themename="darkly")
    root.geometry("400x300")
    
    print("✅ 主視窗創建成功")
    
    # 添加測試按鈕
    print("\n📝 添加測試按鈕...")
    
    def open_combat():
        """測試開啟戰鬥視窗"""
        try:
            print("\n🎮 開啟智能戰鬥視窗...")
            combat_window = tb.Toplevel(root)
            combat_window.withdraw()
            
            app = SmartAutoCombatUI(parent_window=combat_window)
            combat_window.deiconify()
            
            print("✅ 智能戰鬥視窗已開啟!")
            
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    tb.Label(
        root,
        text="ChroLens Mimic 整合測試",
        font=("", 16, "bold")
    ).pack(pady=20)
    
    tb.Label(
        root,
        text="點擊按鈕測試開啟智能戰鬥視窗"
    ).pack(pady=10)
    
    tb.Button(
        root,
        text="🎮 開啟智能戰鬥",
        command=open_combat,
        bootstyle="success",
        width=20
    ).pack(pady=20)
    
    tb.Label(
        root,
        text="關閉此視窗即結束測試",
        font=("", 8)
    ).pack(side="bottom", pady=10)
    
    print("✅ 測試介面創建完成")
    print("\n" + "=" * 60)
    print("📌 請點擊「開啟智能戰鬥」按鈕測試")
    print("=" * 60)
    
    root.mainloop()
    
except Exception as e:
    print(f"\n❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    input("\n按 Enter 退出...")
