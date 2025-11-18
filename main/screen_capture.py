# -*- coding: utf-8 -*-
"""
螢幕截圖工具
提供區域選擇截圖功能
"""

import tkinter as tk
from PIL import ImageGrab, Image
import os


class ScreenCaptureSelector:
    """螢幕區域選擇器"""
    
    def __init__(self, callback=None):
        """
        初始化螢幕截圖選擇器
        
        Args:
            callback: 截圖完成後的回調函數,接收 PIL.Image 物件
        """
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.root = None
        self.canvas = None
        self.screenshot = None
        
    def start_selection(self):
        """開始選擇截圖區域"""
        # 先截取整個螢幕
        self.screenshot = ImageGrab.grab()
        
        # 建立全螢幕視窗
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)  # 半透明
        self.root.attributes('-topmost', True)
        self.root.configure(cursor='cross')
        
        # 建立 Canvas
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        self.canvas = tk.Canvas(
            self.root,
            width=screen_width,
            height=screen_height,
            highlightthickness=0,
            bg='black'
        )
        self.canvas.pack()
        
        # 提示文字
        self.canvas.create_text(
            screen_width // 2,
            50,
            text="拖曳滑鼠框選驗證碼區域 (按 ESC 取消)",
            fill='white',
            font=('Microsoft JhengHei', 16, 'bold')
        )
        
        # 綁定滑鼠事件
        self.canvas.bind('<ButtonPress-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)
        self.root.bind('<Escape>', self._on_cancel)
        
        self.root.mainloop()
        
    def _on_press(self, event):
        """滑鼠按下"""
        self.start_x = event.x
        self.start_y = event.y
        
        # 建立矩形
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        self.rect_id = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.start_x,
            self.start_y,
            outline='red',
            width=3
        )
        
    def _on_drag(self, event):
        """滑鼠拖曳"""
        if self.rect_id:
            # 更新矩形
            self.canvas.coords(
                self.rect_id,
                self.start_x,
                self.start_y,
                event.x,
                event.y
            )
            
    def _on_release(self, event):
        """滑鼠放開"""
        end_x = event.x
        end_y = event.y
        
        # 確保座標正確 (左上角 -> 右下角)
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        # 檢查是否有效區域 (至少 10x10 像素)
        if (x2 - x1) < 10 or (y2 - y1) < 10:
            self.root.destroy()
            return
        
        # 截取選定區域
        cropped = self.screenshot.crop((x1, y1, x2, y2))
        
        # 關閉視窗
        self.root.destroy()
        
        # 執行回調
        if self.callback:
            self.callback(cropped)
            
    def _on_cancel(self, event):
        """取消選擇"""
        self.root.destroy()


def capture_screen_region(callback=None):
    """
    啟動螢幕區域選擇
    
    Args:
        callback: 截圖完成後的回調函數,接收 PIL.Image 物件
    """
    selector = ScreenCaptureSelector(callback)
    selector.start_selection()


# 測試用
if __name__ == "__main__":
    def test_callback(image):
        """測試回調"""
        print(f"截圖完成: {image.size}")
        image.save("test_capture.png")
        print("已儲存為 test_capture.png")
    
    capture_screen_region(test_callback)
