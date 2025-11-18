# -*- coding: utf-8 -*-
"""
響應式佈局輔助模組 (Responsive Layout Helper)
為 Tkinter 視窗提供自動調整大小的功能
"""

import tkinter as tk


def make_window_responsive(window, min_width=800, min_height=600, max_screen_ratio=0.9):
    """
    讓 Tkinter 視窗支援響應式佈局 (Responsive Layout)
    
    參數:
        window: Tkinter 視窗物件 (Tk 或 Toplevel)
        min_width: 最小寬度 (預設 800)
        min_height: 最小高度 (預設 600)
        max_screen_ratio: 視窗最大佔螢幕比例 (預設 0.9 = 90%)
    
    功能:
        - 設定最小尺寸
        - 允許使用者調整大小
        - 視窗內容變化時自動調整
    """
    # 設定最小尺寸
    window.minsize(min_width, min_height)
    
    # 允許調整大小
    window.resizable(True, True)
    
    # 更新所有待處理的 GUI 事件
    window.update_idletasks()
    
    # 儲存螢幕比例參數
    window._responsive_max_ratio = max_screen_ratio
    
    return window


def auto_resize_window(window, required_width=None, required_height=None, center=True):
    """
    根據內容自動調整視窗大小
    
    參數:
        window: Tkinter 視窗物件
        required_width: 需要的寬度 (None = 自動計算)
        required_height: 需要的高度 (None = 自動計算)
        center: 是否將視窗置中 (預設 True)
    
    使用範例:
        auto_resize_window(window)  # 自動計算並調整
        auto_resize_window(window, 1000, 700)  # 調整為指定大小
    """
    # 更新所有待處理的 GUI 事件
    window.update_idletasks()
    
    # 取得螢幕尺寸
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # 取得最大視窗比例
    max_ratio = getattr(window, '_responsive_max_ratio', 0.9)
    max_window_width = int(screen_width * max_ratio)
    max_window_height = int(screen_height * max_ratio)
    
    # 計算需要的尺寸
    if required_width is None:
        # 自動計算：根據內容需求
        required_width = window.winfo_reqwidth()
    
    if required_height is None:
        # 自動計算：根據內容需求
        required_height = window.winfo_reqheight()
    
    # 取得最小尺寸限制
    min_width = window.winfo_reqwidth() if hasattr(window, 'minsize') else 800
    min_height = window.winfo_reqheight() if hasattr(window, 'minsize') else 600
    
    # 確保在合理範圍內
    new_width = max(min_width, min(required_width, max_window_width))
    new_height = max(min_height, min(required_height, max_window_height))
    
    # 計算視窗位置（置中）
    if center:
        x = (screen_width - new_width) // 2
        y = (screen_height - new_height) // 2
        window.geometry(f"{new_width}x{new_height}+{x}+{y}")
    else:
        window.geometry(f"{new_width}x{new_height}")
    
    window.update_idletasks()


def adjust_window_to_content(window, padding=50):
    """
    讓視窗自動調整到剛好容納所有內容
    
    參數:
        window: Tkinter 視窗物件
        padding: 額外的邊距 (預設 50)
    
    使用時機:
        - 載入大圖片後
        - 動態新增內容後
        - 訊息內容變長後
    """
    window.update_idletasks()
    
    # 取得當前內容需要的尺寸
    req_width = window.winfo_reqwidth() + padding
    req_height = window.winfo_reqheight() + padding
    
    # 取得當前視窗尺寸
    current_width = window.winfo_width()
    current_height = window.winfo_height()
    
    # 只在需要時才調整（內容變大時）
    if req_width > current_width or req_height > current_height:
        auto_resize_window(window, req_width, req_height, center=True)


def bind_responsive_layout(window):
    """
    綁定事件，讓視窗在內容變化時自動調整
    
    參數:
        window: Tkinter 視窗物件
    
    功能:
        - 監聽視窗內容變化
        - 自動觸發尺寸調整
    """
    def on_configure(event):
        """內容變化時的回調"""
        if event.widget == window:
            # 檢查是否需要調整視窗大小
            window.update_idletasks()
    
    # 綁定 Configure 事件
    window.bind("<Configure>", on_configure)


class ResponsiveFrame(tk.Frame):
    """
    響應式 Frame
    會根據內容自動調整父視窗大小
    """
    
    def __init__(self, parent, auto_adjust=True, **kwargs):
        super().__init__(parent, **kwargs)
        self.auto_adjust = auto_adjust
        self.parent_window = self._get_toplevel()
        
        if auto_adjust and self.parent_window:
            # 綁定內容變化事件
            self.bind("<Configure>", self._on_content_change)
    
    def _get_toplevel(self):
        """取得最上層視窗"""
        widget = self
        while widget:
            if isinstance(widget, (tk.Tk, tk.Toplevel)):
                return widget
            widget = widget.master
        return None
    
    def _on_content_change(self, event):
        """內容變化時自動調整視窗"""
        if self.auto_adjust and self.parent_window:
            self.after(100, lambda: adjust_window_to_content(self.parent_window))


class ResponsiveDialog(tk.Toplevel):
    """
    響應式對話框
    自動根據內容調整大小
    """
    
    def __init__(self, parent, min_width=400, min_height=300, **kwargs):
        super().__init__(parent, **kwargs)
        
        # 啟用響應式佈局
        make_window_responsive(self, min_width, min_height)
        
        # 綁定響應式行為
        bind_responsive_layout(self)
    
    def show_and_adjust(self):
        """顯示對話框並自動調整大小"""
        self.update_idletasks()
        adjust_window_to_content(self)
        self.deiconify()


def create_scrollable_responsive_frame(parent, **kwargs):
    """
    創建可捲動的響應式 Frame
    
    參數:
        parent: 父容器
        **kwargs: 其他 Frame 參數
    
    返回:
        (canvas, scrollbar, inner_frame) 元組
    
    使用範例:
        canvas, scrollbar, frame = create_scrollable_responsive_frame(parent)
        # 在 frame 中添加內容
        tk.Label(frame, text="內容").pack()
    """
    # 創建 Canvas
    canvas = tk.Canvas(parent, **kwargs)
    canvas.pack(side="left", fill="both", expand=True)
    
    # 創建 Scrollbar
    scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    
    # 配置 Canvas
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # 創建內部 Frame
    inner_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=inner_frame, anchor="nw")
    
    # 綁定內容變化事件
    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    inner_frame.bind("<Configure>", on_frame_configure)
    
    return canvas, scrollbar, inner_frame


# ====== 使用範例 ======

def example_responsive_window():
    """範例：創建響應式視窗"""
    root = tk.Tk()
    root.title("響應式視窗範例")
    
    # 啟用響應式佈局
    make_window_responsive(root, min_width=600, min_height=400)
    
    # 創建內容
    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    tk.Label(frame, text="這是一個響應式視窗", font=("Arial", 16)).pack(pady=10)
    
    # 動態新增內容的按鈕
    def add_content():
        tk.Label(frame, text="新增的內容" * 10).pack(pady=5)
        # 內容變化後自動調整視窗
        adjust_window_to_content(root)
    
    tk.Button(frame, text="新增內容", command=add_content).pack(pady=10)
    
    root.mainloop()


def example_responsive_dialog():
    """範例：響應式對話框"""
    root = tk.Tk()
    root.withdraw()
    
    # 創建響應式對話框
    dialog = ResponsiveDialog(root, min_width=500, min_height=300)
    dialog.title("響應式對話框")
    
    # 添加內容
    tk.Label(dialog, text="這是響應式對話框", font=("Arial", 14)).pack(pady=20)
    tk.Text(dialog, height=10, width=50).pack(padx=20, pady=10)
    tk.Button(dialog, text="關閉", command=dialog.destroy).pack(pady=10)
    
    # 顯示並自動調整
    dialog.show_and_adjust()
    
    root.mainloop()


if __name__ == "__main__":
    print("響應式佈局輔助模組")
    print("提供以下功能:")
    print("1. make_window_responsive() - 啟用響應式佈局")
    print("2. auto_resize_window() - 自動調整視窗大小")
    print("3. adjust_window_to_content() - 根據內容調整")
    print("4. ResponsiveFrame - 響應式 Frame")
    print("5. ResponsiveDialog - 響應式對話框")
    print()
    print("執行範例:")
    # example_responsive_window()
    # example_responsive_dialog()
