# -*- coding: utf-8 -*-
"""
測試截圖功能和自動戰鬥系統整合
"""

import tkinter as tk
import sys
import os

print("=" * 60)
print("ChroLens 截圖功能測試")
print("=" * 60)

# 測試 1: 檢查模組導入
print("\n[測試 1] 檢查模組導入...")
try:
    from screenshot_selector import capture_screen_region
    print("✅ screenshot_selector 模組導入成功")
except Exception as e:
    print(f"❌ screenshot_selector 導入失敗: {e}")
    sys.exit(1)

try:
    from PIL import Image, ImageGrab, ImageTk
    print("✅ PIL 模組導入成功")
except Exception as e:
    print(f"❌ PIL 導入失敗: {e}")
    print("   請安裝: pip install Pillow")
    sys.exit(1)

# 測試 2: 啟動簡單測試界面
print("\n[測試 2] 啟動測試界面...")
print("提示: 點擊按鈕後,在螢幕上拖動選擇區域")

def test_capture(image):
    """截圖回調"""
    print(f"\n✅ 截圖成功!")
    print(f"   尺寸: {image.width} × {image.height}")
    print(f"   格式: {image.mode}")
    
    # 保存截圖
    save_dir = 'test_captures'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    filename = os.path.join(save_dir, 'test_screenshot.png')
    image.save(filename)
    print(f"   已保存至: {filename}")
    
    # 顯示成功訊息
    result_label.config(
        text=f"✅ 截圖成功!\n尺寸: {image.width}×{image.height}\n已保存至: {filename}",
        fg="green"
    )

# 創建測試視窗
root = tk.Tk()
root.title("ChroLens 截圖測試")
root.geometry("400x300")

# 標題
title_label = tk.Label(
    root,
    text="ChroLens 截圖功能測試",
    font=("Microsoft YaHei UI", 16, "bold"),
    pady=20
)
title_label.pack()

# 說明
info_label = tk.Label(
    root,
    text="點擊按鈕後:\n1. 螢幕會變暗並顯示提示\n2. 拖動滑鼠選擇要截圖的區域\n3. 釋放滑鼠完成截圖\n4. 按 ESC 可取消",
    font=("Microsoft YaHei UI", 10),
    fg="blue",
    pady=10
)
info_label.pack()

# 截圖按鈕
capture_btn = tk.Button(
    root,
    text="📸 開始截圖",
    command=lambda: capture_screen_region(test_capture),
    font=("Microsoft YaHei UI", 12, "bold"),
    bg="#4CAF50",
    fg="white",
    width=20,
    height=2,
    cursor="hand2"
)
capture_btn.pack(pady=20)

# 結果顯示
result_label = tk.Label(
    root,
    text="尚未截圖",
    font=("Microsoft YaHei UI", 10),
    fg="gray"
)
result_label.pack()

print("✅ 測試界面已啟動")
print("\n" + "=" * 60)

root.mainloop()
