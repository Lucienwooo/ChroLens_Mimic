# -*- coding: utf-8 -*-
"""
截圖框選工具
讓用戶可以在螢幕上拖動選擇要截圖的區域
"""

import tkinter as tk
from PIL import ImageGrab, ImageTk, Image
import os


class ScreenshotSelector:
    """螢幕截圖框選工具"""
    
    def __init__(self, callback=None):
        """
        初始化截圖選擇器
        
        Args:
            callback: 截圖完成後的回調函數,接收 PIL.Image 對象
        """
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.root = None
        self.canvas = None
        self.screenshot = None
        
    def start(self):
        """開始截圖選擇"""
        # 先截取整個螢幕
        self.screenshot = ImageGrab.grab()
        
        # 創建全螢幕視窗
        self.root = tk.Toplevel()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.attributes('-topmost', True)
        self.root.configure(cursor='cross')
        
        # 創建畫布
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        self.canvas = tk.Canvas(
            self.root,
            width=screen_width,
            height=screen_height,
            highlightthickness=0,
            cursor='cross'
        )
        self.canvas.pack()
        
        # 顯示截圖作為背景
        screenshot_resized = self.screenshot.resize((screen_width, screen_height))
        self.bg_image = ImageTk.PhotoImage(screenshot_resized)
        self.canvas.create_image(0, 0, image=self.bg_image, anchor='nw')
        
        # 添加半透明遮罩
        self.canvas.create_rectangle(
            0, 0, screen_width, screen_height,
            fill='black',
            stipple='gray50',
            tags='mask'
        )
        
        # 添加提示文字
        self.canvas.create_text(
            screen_width // 2,
            50,
            text='拖動滑鼠選擇截圖區域 | ESC 取消',
            font=('Microsoft YaHei UI', 16, 'bold'),
            fill='yellow',
            tags='hint'
        )
        
        # 綁定事件
        self.canvas.bind('<Button-1>', self._on_mouse_down)
        self.canvas.bind('<B1-Motion>', self._on_mouse_move)
        self.canvas.bind('<ButtonRelease-1>', self._on_mouse_up)
        self.root.bind('<Escape>', lambda e: self._cancel())
        
    def _on_mouse_down(self, event):
        """滑鼠按下"""
        self.start_x = event.x
        self.start_y = event.y
        
        # 清除提示文字
        self.canvas.delete('hint')
        
        # 創建選擇矩形
        if self.rect:
            self.canvas.delete(self.rect)
        
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red',
            width=2,
            dash=(5, 5),
            tags='selection'
        )
        
    def _on_mouse_move(self, event):
        """滑鼠拖動"""
        if self.start_x is None:
            return
            
        # 更新矩形
        self.canvas.coords(
            self.rect,
            self.start_x, self.start_y,
            event.x, event.y
        )
        
        # 顯示尺寸
        width = abs(event.x - self.start_x)
        height = abs(event.y - self.start_y)
        
        # 刪除舊的尺寸標籤
        self.canvas.delete('size_label')
        
        # 創建新的尺寸標籤
        self.canvas.create_text(
            (self.start_x + event.x) // 2,
            (self.start_y + event.y) // 2,
            text=f'{width} × {height}',
            font=('Microsoft YaHei UI', 12, 'bold'),
            fill='yellow',
            tags='size_label'
        )
        
    def _on_mouse_up(self, event):
        """滑鼠釋放"""
        if self.start_x is None:
            return
            
        end_x = event.x
        end_y = event.y
        
        # 計算選擇區域
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        # 檢查是否選擇了有效區域
        if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
            self._cancel()
            return
        
        # 從原始截圖中裁剪選擇區域
        # 需要將視窗座標轉換為螢幕座標
        screen_width = self.screenshot.width
        screen_height = self.screenshot.height
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # 計算縮放比例
        scale_x = screen_width / canvas_width
        scale_y = screen_height / canvas_height
        
        # 轉換座標
        crop_x1 = int(x1 * scale_x)
        crop_y1 = int(y1 * scale_y)
        crop_x2 = int(x2 * scale_x)
        crop_y2 = int(y2 * scale_y)
        
        # 裁剪圖片
        cropped = self.screenshot.crop((crop_x1, crop_y1, crop_x2, crop_y2))
        
        # 關閉視窗
        self.root.destroy()
        
        # 調用回調
        if self.callback:
            self.callback(cropped)
            
    def _cancel(self):
        """取消截圖"""
        if self.root:
            self.root.destroy()


def capture_screen_region(callback=None):
    """
    啟動螢幕區域選擇器
    
    Args:
        callback: 截圖完成後的回調函數,接收 PIL.Image 對象
    
    Example:
        def on_capture(image):
            image.save('screenshot.png')
            print('截圖已保存')
        
        capture_screen_region(on_capture)
    """
    selector = ScreenshotSelector(callback)
    selector.start()


if __name__ == '__main__':
    # 測試
    def test_callback(image):
        filename = 'test_screenshot.png'
        image.save(filename)
        print(f'截圖已保存為 {filename}')
        print(f'尺寸: {image.width} × {image.height}')
    
    root = tk.Tk()
    root.title('截圖測試')
    root.geometry('300x200')
    
    tk.Button(
        root,
        text='開始截圖',
        command=lambda: capture_screen_region(test_callback),
        font=('Microsoft YaHei UI', 12),
        width=15,
        height=2
    ).pack(expand=True)
    
    root.mainloop()
