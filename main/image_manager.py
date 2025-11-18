# -*- coding: utf-8 -*-
"""
ChroLens 圖片管理器
管理、測試、截圖模板圖片
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from PIL import Image, ImageTk
import threading
import sys
import io

# ✅ 導入響應式佈局模組
try:
    from responsive_layout import make_window_responsive, adjust_window_to_content
except ImportError:
    # 如果模組不存在，提供簡單的 fallback
    def make_window_responsive(window, *args, **kwargs):
        window.resizable(True, True)
        return window
    def adjust_window_to_content(window, *args, **kwargs):
        window.update_idletasks()

# ✅ 導入螢幕截圖模組
try:
    from screen_capture import capture_screen_region
except ImportError:
    capture_screen_region = None

# ✅ 導入 ddddocr (驗證碼識別專用庫)
try:
    import ddddocr
    DDDDOCR_AVAILABLE = True
    print("✅ ddddocr 已載入 (驗證碼識別增強)")
except ImportError:
    DDDDOCR_AVAILABLE = False
    print("⚠️ ddddocr 未安裝,使用 Tesseract 作為備用方案")


class ImageManager(tk.Toplevel):
    """圖片管理器視窗"""
    
    def __init__(self, parent=None, image_dir=None):
        super().__init__(parent)
        
        self.parent = parent
        self.image_dir = image_dir or os.path.join(os.path.dirname(__file__), "images", "templates")
        
        # 確保目錄存在
        os.makedirs(self.image_dir, exist_ok=True)
        
        self.title("圖片管理器")
        self.geometry("800x600")
        
        self.selected_image = None
        self.image_list = []
        
        # ✅ 初始化 ddddocr 引擎 (如果可用)
        self.ddddocr_engine = None
        if DDDDOCR_AVAILABLE:
            try:
                self.ddddocr_engine = ddddocr.DdddOcr(show_ad=False)
                print("✅ ddddocr 引擎初始化成功")
            except Exception as e:
                print(f"⚠️ ddddocr 初始化失敗: {e}")
        
        # 設定為模態視窗並保持在最上層
        self.transient(parent)
        self.grab_set()
        
        # ✅ 啟用響應式佈局 (Responsive Layout / Adaptive Window)
        # 這個功能會讓視窗根據內容自動調整大小
        make_window_responsive(self, min_width=800, min_height=600, max_screen_ratio=0.9)
        
        self._create_ui()
        self._load_images()
        
        # 置頂顯示
        self.lift()
        self.focus_force()
        
        # 確保視窗完全顯示後再置頂
        self.after(100, self.lift)
        self.after(100, self.focus_force)
    
    def _create_ui(self):
        """創建UI"""
        # 頂部工具列
        toolbar = tk.Frame(self, bg="#f0f0f0", height=50)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        tk.Label(
            toolbar,
            text="📸 圖片管理器",
            font=("Microsoft JhengHei", 12, "bold"),
            bg="#f0f0f0"
        ).pack(side="left", padx=10)
        
        tk.Button(
            toolbar,
            text="📂 匯入圖片",
            command=self._import_image,
            bg="#2196F3",
            fg="white",
            font=("Microsoft JhengHei", 9, "bold"),
            padx=10,
            pady=5
        ).pack(side="right", padx=5)
        
        tk.Button(
            toolbar,
            text="✂️ 截圖",
            command=self._capture_screenshot,
            bg="#4CAF50",
            fg="white",
            font=("Microsoft JhengHei", 9, "bold"),
            padx=10,
            pady=5
        ).pack(side="right", padx=5)
        
        tk.Button(
            toolbar,
            text="🔄 重新整理",
            command=self._load_images,
            bg="#FF9800",
            fg="white",
            font=("Microsoft JhengHei", 9, "bold"),
            padx=10,
            pady=5
        ).pack(side="right", padx=5)
        
        # 主要內容區
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 左側: 圖片列表
        left_frame = tk.Frame(main_frame, width=250)
        left_frame.pack(side="left", fill="both", padx=(0, 5))
        left_frame.pack_propagate(False)
        
        tk.Label(
            left_frame,
            text="📋 圖片列表",
            font=("Microsoft JhengHei", 10, "bold")
        ).pack(anchor="w", pady=5)
        
        # 列表框架
        list_container = tk.Frame(left_frame)
        list_container.pack(fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side="right", fill="y")
        
        self.image_listbox = tk.Listbox(
            list_container,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 9),
            selectmode=tk.SINGLE
        )
        self.image_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.image_listbox.yview)
        
        self.image_listbox.bind("<<ListboxSelect>>", self._on_select_image)
        self.image_listbox.bind("<Double-Button-1>", self._on_double_click)
        
        # 右側: 預覽和操作
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True)
        
        # 預覽區
        preview_frame = tk.LabelFrame(
            right_frame,
            text="🖼️ 圖片預覽",
            font=("Microsoft JhengHei", 10, "bold")
        )
        preview_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.preview_label = tk.Label(
            preview_frame,
            text="請選擇一個圖片",
            bg="#f5f5f5",
            font=("Microsoft JhengHei", 10),
            fg="#999"
        )
        self.preview_label.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 資訊區
        info_frame = tk.LabelFrame(
            right_frame,
            text="ℹ️ 圖片資訊",
            font=("Microsoft JhengHei", 10, "bold")
        )
        info_frame.pack(fill="x", pady=(0, 10))
        
        self.info_label = tk.Label(
            info_frame,
            text="",
            font=("Consolas", 9),
            justify="left",
            anchor="w",
            padx=10,
            pady=10
        )
        self.info_label.pack(fill="x")
        
        # ✨ 驗證碼識別區
        engine_status = "ddddocr ✨" if self.ddddocr_engine else "Tesseract"
        captcha_frame = tk.LabelFrame(
            info_frame,
            text=f"🔤 驗證碼識別 ({engine_status})",
            font=("Microsoft JhengHei", 10, "bold")
        )
        captcha_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # 驗證碼文字框（可複製）
        captcha_text_frame = tk.Frame(captcha_frame)
        captcha_text_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        tk.Label(
            captcha_text_frame,
            text="識別結果:",
            font=("Microsoft JhengHei", 9)
        ).pack(side="left")
        
        self.captcha_result_var = tk.StringVar(value="")
        self.captcha_entry = tk.Entry(
            captcha_text_frame,
            textvariable=self.captcha_result_var,
            font=("Consolas", 14, "bold"),  # 增大字體
            fg="#00FF00",  # 綠色字體 (在黑底上更清楚)
            bg="#000000",  # 黑色背景
            state="readonly",
            readonlybackground="#000000",  # readonly 狀態也是黑色背景
            disabledforeground="#00FF00",  # disabled 狀態的字體顏色
            insertbackground="#00FF00",  # 游標顏色
            selectbackground="#333333",  # 選取時的背景
            selectforeground="#00FF00",  # 選取時的字體
            relief="sunken",  # 凹陷邊框效果
            bd=2,  # 邊框寬度
            justify="center"
        )
        self.captcha_entry.pack(side="left", fill="x", expand=True, padx=10)
        
        # 複製按鈕
        tk.Button(
            captcha_text_frame,
            text="📋",
            command=self._copy_captcha,
            font=("Microsoft JhengHei", 9),
            width=3,
            bg="#E3F2FD"
        ).pack(side="left")
        
        # 識別按鈕框架
        recognize_btn_frame = tk.Frame(captcha_frame)
        recognize_btn_frame.pack(pady=(5, 10), padx=10, fill="x")
        
        # 識別檔案按鈕
        tk.Button(
            recognize_btn_frame,
            text="🔍 識別選定圖片",
            command=self._recognize_captcha,
            bg="#4CAF50",
            fg="white",
            font=("Microsoft JhengHei", 9, "bold"),
            padx=15,
            pady=5
        ).pack(side="left", padx=5, expand=True, fill="x")
        
        # 螢幕截圖識別按鈕
        tk.Button(
            recognize_btn_frame,
            text="📸 截圖識別",
            command=self._capture_and_recognize,
            bg="#FF9800",
            fg="white",
            font=("Microsoft JhengHei", 9, "bold"),
            padx=15,
            pady=5
        ).pack(side="left", padx=5, expand=True, fill="x")
        
        # 操作按鈕區
        button_frame = tk.Frame(right_frame)
        button_frame.pack(fill="x")
        
        tk.Button(
            button_frame,
            text="🔍 測試識別",
            command=self._test_recognition,
            bg="#9C27B0",
            fg="white",
            font=("Microsoft JhengHei", 9, "bold"),
            padx=15,
            pady=8
        ).pack(side="left", padx=5)
        
        tk.Button(
            button_frame,
            text="📝 重新命名",
            command=self._rename_image,
            bg="#FF9800",
            fg="white",
            font=("Microsoft JhengHei", 9, "bold"),
            padx=15,
            pady=8
        ).pack(side="left", padx=5)
        
        tk.Button(
            button_frame,
            text="🗑️ 刪除",
            command=self._delete_image,
            bg="#F44336",
            fg="white",
            font=("Microsoft JhengHei", 9, "bold"),
            padx=15,
            pady=8
        ).pack(side="left", padx=5)
        
        # 底部狀態列
        self.status_label = tk.Label(
            self,
            text="✅ 就緒",
            font=("Microsoft JhengHei", 9),
            bg="#e8f5e9",
            fg="#2e7d32",
            anchor="w",
            padx=10,
            pady=5
        )
        self.status_label.pack(fill="x", side="bottom")
    
    def _load_images(self):
        """載入圖片列表"""
        self.image_listbox.delete(0, tk.END)
        self.image_list = []
        
        try:
            for file in sorted(os.listdir(self.image_dir)):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    self.image_listbox.insert(tk.END, file)
                    self.image_list.append(os.path.join(self.image_dir, file))
            
            count = len(self.image_list)
            self.status_label.config(
                text=f"✅ 已載入 {count} 個圖片",
                bg="#e8f5e9",
                fg="#2e7d32"
            )
        except Exception as e:
            messagebox.showerror("錯誤", f"載入圖片列表失敗:\n{e}")
    
    def _on_select_image(self, event=None):
        """選擇圖片時"""
        selection = self.image_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        self.selected_image = self.image_list[index]
        
        # 顯示預覽
        self._show_preview(self.selected_image)
        
        # 顯示資訊
        self._show_info(self.selected_image)
    
    def _show_preview(self, image_path):
        """顯示圖片預覽 - 支援響應式佈局 (Responsive Layout)"""
        try:
            image = Image.open(image_path)
            original_width, original_height = image.size
            
            # ✅ 動態計算適合的預覽尺寸
            # 根據圖片大小決定預覽區域大小
            if original_width > 800 or original_height > 600:
                # 大圖片：使用較大的預覽區域
                max_size = (700, 525)
            elif original_width > 400 or original_height > 300:
                # 中等圖片：使用中等預覽區域
                max_size = (500, 375)
            else:
                # 小圖片：使用標準預覽區域
                max_size = (400, 300)
            
            # 縮放圖片
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            preview_width, preview_height = image.size
            
            photo = ImageTk.PhotoImage(image)
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # 保持引用
            
            # ✅ 使用響應式佈局自動調整視窗
            # 這會確保所有內容都可見，不會被擠出視窗外
            self.after(100, lambda: adjust_window_to_content(self, padding=100))
            
        except Exception as e:
            self.preview_label.config(
                text=f"無法載入圖片\n{e}",
                image="",
                fg="#F44336"
            )
    
    def _show_info(self, image_path):
        """顯示圖片資訊"""
        try:
            image = Image.open(image_path)
            size = os.path.getsize(image_path)
            
            info = f"檔名: {os.path.basename(image_path)}\n"
            info += f"尺寸: {image.width} x {image.height} px\n"
            info += f"大小: {size / 1024:.1f} KB\n"
            info += f"格式: {image.format}"
            
            self.info_label.config(text=info)
        except Exception as e:
            self.info_label.config(text=f"讀取資訊失敗: {e}")
    
    def _on_double_click(self, event=None):
        """雙擊圖片時"""
        if self.selected_image:
            self._test_recognition()
    
    def _import_image(self):
        """匯入圖片"""
        file_path = filedialog.askopenfilename(
            title="選擇圖片",
            filetypes=[
                ("圖片檔案", "*.png *.jpg *.jpeg *.bmp"),
                ("所有檔案", "*.*")
            ]
        )
        
        if file_path:
            try:
                # 複製到圖片目錄
                import shutil
                dest = os.path.join(self.image_dir, os.path.basename(file_path))
                shutil.copy2(file_path, dest)
                
                self._load_images()
                messagebox.showinfo("成功", "圖片已匯入!")
            except Exception as e:
                messagebox.showerror("錯誤", f"匯入圖片失敗:\n{e}")
    
    def _capture_screenshot(self):
        """截圖功能"""
        messagebox.showinfo(
            "截圖功能",
            "截圖功能開發中...\n\n"
            "預計功能:\n"
            "1. 全螢幕截圖\n"
            "2. 區域選擇截圖\n"
            "3. 延遲截圖\n"
            "4. 自動命名和保存"
        )
    
    def _test_recognition(self):
        """測試圖片識別 - 增強版"""
        if not self.selected_image:
            messagebox.showwarning("警告", "請先選擇一個圖片")
            return
        
        # 顯示測試對話框
        test_dialog = tk.Toplevel(self)
        test_dialog.title("測試圖片識別")
        test_dialog.geometry("500x400")
        test_dialog.transient(self)
        
        tk.Label(
            test_dialog,
            text="🔍 正在測試圖片識別...",
            font=("Microsoft JhengHei", 11, "bold"),
            pady=20
        ).pack()
        
        result_text = tk.Text(
            test_dialog,
            font=("Consolas", 9),
            wrap="word",
            height=15
        )
        result_text.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Button(
            test_dialog,
            text="關閉",
            command=test_dialog.destroy,
            padx=20,
            pady=5
        ).pack(pady=10)
        
        # 在背景執行測試
        def run_test():
            try:
                from image_recognition import ImageRecognition
                import cv2
                
                result_text.insert("1.0", f"測試圖片: {os.path.basename(self.selected_image)}\n")
                result_text.insert("end", "=" * 50 + "\n\n")
                
                # 驗證檔案
                result_text.insert("end", "📁 驗證檔案...\n")
                result_text.insert("end", f"路徑: {self.selected_image}\n")
                result_text.insert("end", f"存在: {'✓' if os.path.exists(self.selected_image) else '✗'}\n\n")
                
                # 使用新的ImageRecognition (支援中文路徑)
                ir = ImageRecognition(confidence=0.75)
                
                # 測試圖片載入
                result_text.insert("end", "🖼️ 測試圖片載入...\n")
                test_dialog.update()
                
                template = ir._load_template(self.selected_image)
                if template is None:
                    result_text.insert("end", "✗ 圖片載入失敗\n")
                    result_text.insert("end", "可能原因:\n")
                    result_text.insert("end", "1. 圖片檔案損壞\n")
                    result_text.insert("end", "2. 不支援的圖片格式\n")
                    result_text.insert("end", "3. 檔案權限問題\n\n")
                    result_text.insert("end", "建議: 重新保存為PNG格式\n")
                    return
                else:
                    h, w = template.shape[:2]
                    result_text.insert("end", f"✓ 圖片載入成功 ({w}x{h} px)\n\n")
                
                # 測試找圖 (多種信心度)
                result_text.insert("end", "🔍 開始搜尋圖片...\n")
                result_text.insert("end", "(這可能需要幾秒鐘)\n\n")
                test_dialog.update()
                
                location = ir.find_image(self.selected_image, multi_scale=True, grayscale=True)
                
                if location:
                    x, y, w, h = location
                    center = ir.get_image_center(location)
                    result_text.insert("end", f"✅ 成功找到圖片!\n\n")
                    result_text.insert("end", f"📍 位置: ({x}, {y})\n")
                    result_text.insert("end", f"📏 尺寸: {w} x {h} px\n")
                    result_text.insert("end", f"🎯 中心點: {center}\n\n")
                    result_text.insert("end", f"💡 在文字指令中使用:\n")
                    result_text.insert("end", f">點擊圖片[{os.path.basename(self.selected_image)}]\n")
                else:
                    result_text.insert("end", "❌ 未找到圖片\n\n")
                    result_text.insert("end", "💡 建議:\n")
                    result_text.insert("end", "1. 確認圖片在螢幕上可見\n")
                    result_text.insert("end", "2. 圖片可能被遮擋或縮放\n")
                    result_text.insert("end", "3. 嘗試截取更小範圍的圖片\n")
                    result_text.insert("end", "4. 確保圖片格式為PNG\n")
                    result_text.insert("end", "5. 避免檔名包含特殊字元\n")
                
            except ImportError as ie:
                result_text.insert("1.0", f"❌ 缺少必要套件: {ie}\n\n")
                result_text.insert("end", "請執行以下命令安裝:\n")
                result_text.insert("end", "pip install pyautogui opencv-python numpy pillow\n")
            except Exception as e:
                result_text.insert("end", f"\n❌ 測試過程發生錯誤:\n{e}\n")
                import traceback
                result_text.insert("end", f"\n詳細錯誤:\n{traceback.format_exc()}\n")
        
        # 啟動測試線程
        threading.Thread(target=run_test, daemon=True).start()
    
    def _rename_image(self):
        """重新命名圖片"""
        if not self.selected_image:
            messagebox.showwarning("警告", "請先選擇一個圖片")
            return
        
        old_name = os.path.basename(self.selected_image)
        new_name = tk.simpledialog.askstring(
            "重新命名",
            f"請輸入新的檔名:\n(原檔名: {old_name})",
            initialvalue=old_name
        )
        
        if new_name and new_name != old_name:
            try:
                new_path = os.path.join(self.image_dir, new_name)
                os.rename(self.selected_image, new_path)
                self._load_images()
                messagebox.showinfo("成功", "重新命名成功!")
            except Exception as e:
                messagebox.showerror("錯誤", f"重新命名失敗:\n{e}")
    
    def _delete_image(self):
        """刪除圖片"""
        if not self.selected_image:
            messagebox.showwarning("警告", "請先選擇一個圖片")
            return
        
        filename = os.path.basename(self.selected_image)
        if messagebox.askyesno("確認刪除", f"確定要刪除圖片嗎?\n\n{filename}"):
            try:
                os.remove(self.selected_image)
                self._load_images()
                self.preview_label.config(image="", text="請選擇一個圖片")
                self.info_label.config(text="")
                messagebox.showinfo("成功", "圖片已刪除!")
            except Exception as e:
                messagebox.showerror("錯誤", f"刪除圖片失敗:\n{e}")
    
    def _copy_captcha(self):
        """複製驗證碼到剪貼簿"""
        result = self.captcha_result_var.get()
        if result:
            self.clipboard_clear()
            self.clipboard_append(result)
            self.status_label.config(
                text=f"✅ 已複製驗證碼: {result}",
                bg="#e8f5e9",
                fg="#2e7d32"
            )
        else:
            messagebox.showwarning("警告", "沒有可複製的驗證碼")
    
    def _capture_and_recognize(self):
        """螢幕截圖並識別驗證碼"""
        if capture_screen_region is None:
            messagebox.showerror("錯誤", "螢幕截圖模組未載入")
            return
        
        # ✅ 臨時解除 transient 和 grab，才能隱藏視窗
        if self.parent:
            self.transient("")  # 解除 transient
        self.grab_release()  # 解除 grab
        
        # 隱藏視窗以便截圖
        self.withdraw()  # 使用 withdraw 而非 iconify
        self.update()
        
        # 短暫延遲確保視窗完全隱藏
        self.after(200, self._start_screen_capture)
    
    def _start_screen_capture(self):
        """啟動螢幕截圖"""
        def on_capture_complete(image):
            """截圖完成回調"""
            # 還原視窗並重新設定為模態
            self.deiconify()  # 顯示視窗
            if self.parent:
                self.transient(self.parent)  # 重新設定 transient
            self.grab_set()  # 重新設定 grab
            self.lift()  # 提升到最上層
            self.focus_force()  # 強制取得焦點
            self.update()
            
            # 執行 OCR 識別
            self._recognize_image_data(image)
        
        # 啟動區域選擇
        try:
            capture_screen_region(on_capture_complete)
        except Exception as e:
            # 發生錯誤時也要還原視窗設定
            self.deiconify()
            if self.parent:
                self.transient(self.parent)
            self.grab_set()
            self.lift()
            self.focus_force()
            messagebox.showerror("錯誤", f"截圖失敗:\n{e}")
    
    def _recognize_captcha(self):
        """識別當前圖片中的驗證碼"""
        if not self.selected_image:
            messagebox.showwarning("警告", "請先選擇一個圖片")
            return
        
        # 使用檔案路徑識別
        self._recognize_image_data(self.selected_image)
    
    def _recognize_image_data(self, image_source):
        """
        識別圖片中的驗證碼 (通用方法)
        
        Args:
            image_source: 圖片來源,可以是:
                         - str: 檔案路徑
                         - PIL.Image: PIL 圖片物件
        """
        # 清空結果
        self.captcha_result_var.set("")
        
        self.status_label.config(
            text="🔍 正在識別驗證碼...",
            bg="#fff3e0",
            fg="#e65100"
        )
        self.update()
        
        # 在背景執行識別
        def run_recognition():
            try:
                import cv2
                import numpy as np
                
                # 檢查是否已安裝 pytesseract
                try:
                    import pytesseract
                    
                    # ✅ 自動設定 Tesseract 路徑並加入系統 PATH
                    import os
                    possible_paths = [
                        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                        r'C:\Tesseract-OCR\tesseract.exe',
                        os.path.expanduser(r'~\AppData\Local\Tesseract-OCR\tesseract.exe'),
                        os.path.expanduser(r'~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'),
                    ]
                    
                    # 尋找有效的 Tesseract 路徑
                    tesseract_found = False
                    tesseract_dir = None
                    
                    for path in possible_paths:
                        if os.path.exists(path):
                            pytesseract.pytesseract.tesseract_cmd = path
                            tesseract_dir = os.path.dirname(path)
                            tesseract_found = True
                            break
                    
                    if not tesseract_found:
                        # 嘗試使用系統 PATH 中的 tesseract
                        import shutil
                        tesseract_path = shutil.which('tesseract')
                        if tesseract_path:
                            tesseract_dir = os.path.dirname(tesseract_path)
                            tesseract_found = True
                        else:
                            raise FileNotFoundError("找不到 Tesseract 執行檔")
                    
                    # ✅ 將 Tesseract 目錄加入 PATH (解決 DLL 缺失問題)
                    if tesseract_dir and tesseract_dir not in os.environ['PATH']:
                        os.environ['PATH'] = tesseract_dir + os.pathsep + os.environ['PATH']
                    
                    use_ocr = True
                except ImportError:
                    use_ocr = False
                except FileNotFoundError:
                    use_ocr = False
                
                # 載入圖片 (支援檔案路徑或 PIL Image)
                if isinstance(image_source, str):
                    # 檔案路徑
                    image = cv2.imread(image_source)
                    if image is None:
                        # 嘗試使用 imdecode 處理中文路徑
                        with open(image_source, 'rb') as f:
                            image_data = f.read()
                        image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
                elif isinstance(image_source, Image.Image):
                    # PIL Image -> numpy array -> OpenCV
                    img_array = np.array(image_source)
                    # RGB -> BGR (OpenCV 格式)
                    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                        image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    else:
                        image = img_array
                else:
                    raise Exception("不支援的圖片格式")
                
                if image is None:
                    raise Exception("無法載入圖片")
                
                # ====== 優先使用 ddddocr (最佳效果) ======
                if self.ddddocr_engine:
                    try:
                        # 將圖片轉為 bytes
                        if isinstance(image_source, str):
                            with open(image_source, 'rb') as f:
                                image_bytes = f.read()
                        elif isinstance(image_source, Image.Image):
                            # PIL Image -> bytes
                            import io
                            buffer = io.BytesIO()
                            image_source.save(buffer, format='PNG')
                            image_bytes = buffer.getvalue()
                        else:
                            # OpenCV image -> bytes
                            is_success, buffer = cv2.imencode(".png", image)
                            if is_success:
                                image_bytes = buffer.tobytes()
                            else:
                                raise Exception("無法編碼圖片")
                        
                        # ddddocr 識別
                        result = self.ddddocr_engine.classification(image_bytes)
                        
                        if result and len(result) >= 3:
                            # 清理結果 (只保留英文和數字)
                            cleaned_result = ''.join(filter(str.isalnum, result))
                            
                            if cleaned_result:
                                # ✅ 使用 after() 在主線程中更新 UI
                                self.after(0, lambda: self.captcha_result_var.set(cleaned_result))
                                self.after(0, lambda: self.status_label.config(
                                    text=f"✅ ddddocr 識別成功: {cleaned_result}",
                                    bg="#e8f5e9",
                                    fg="#2e7d32"
                                ))
                                print(f"🎯 ddddocr: {cleaned_result}")
                                return  # 成功識別,直接返回
                    except Exception as e:
                        print(f"⚠️ ddddocr 識別失敗: {e}, 切換到 Tesseract")
                
                # ====== 備用方案: Tesseract 多策略識別 ======
                if use_ocr:
                    # ====== 多策略識別 (提高成功率) ======
                    all_results = []
                    
                    # 策略 1: 超強放大 + 多次降噪 (針對 76N8 類型)
                    try:
                        if len(image.shape) == 3:
                            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                        else:
                            gray = image
                        
                        # 超強放大 6 倍
                        scale = 600
                        enlarged = cv2.resize(gray, None, fx=scale/100, fy=scale/100, interpolation=cv2.INTER_CUBIC)
                        
                        # 多重降噪
                        denoised1 = cv2.fastNlMeansDenoising(enlarged, None, h=15, templateWindowSize=7, searchWindowSize=21)
                        
                        # 形態學梯度增強邊緣
                        kernel_edge = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                        gradient = cv2.morphologyEx(denoised1, cv2.MORPH_GRADIENT, kernel_edge)
                        
                        # Otsu 二值化
                        blurred = cv2.GaussianBlur(denoised1, (5, 5), 0)
                        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                        
                        # 連續開閉運算
                        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
                        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)
                        
                        # 智能反色
                        if cv2.mean(closed)[0] > 127:
                            cleaned = cv2.bitwise_not(closed)
                        else:
                            cleaned = closed
                        
                        # 再次銳化
                        kernel_sharp = np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]])
                        sharpened = cv2.filter2D(cleaned, -1, kernel_sharp)
                        
                        # 多 PSM 嘗試
                        for psm in [6, 7, 8, 11, 13]:
                            config = f'--psm {psm} --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                            result = pytesseract.image_to_string(sharpened, config=config).strip()
                            if result:
                                all_results.append((''.join(filter(str.isalnum, result)), f'策略1-PSM{psm}'))
                    except:
                        pass
                    
                    # 策略 2: 雙邊濾波 + CLAHE 對比度增強 (針對噪點背景)
                    try:
                        gray2 = gray.copy() if 'gray' in locals() else (cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image)
                        enlarged2 = cv2.resize(gray2, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
                        
                        # 雙邊濾波保留邊緣
                        bilateral = cv2.bilateralFilter(enlarged2, 9, 75, 75)
                        
                        # CLAHE 增強對比度
                        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                        enhanced = clahe.apply(bilateral)
                        
                        # 自適應二值化
                        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
                        adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 3)
                        
                        # 形態學處理
                        kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
                        closed = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel2, iterations=1)
                        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel2, iterations=1)
                        
                        # 反色
                        if cv2.mean(opened)[0] > 127:
                            cleaned2 = cv2.bitwise_not(opened)
                        else:
                            cleaned2 = opened
                        
                        for psm in [6, 7, 8, 11]:
                            config = f'--psm {psm} --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                            result = pytesseract.image_to_string(cleaned2, config=config).strip()
                            if result:
                                all_results.append((''.join(filter(str.isalnum, result)), f'策略2-PSM{psm}'))
                    except:
                        pass
                    
                    # 策略 3: 頂帽變換 + 多閾值融合 (去除背景紋理)
                    try:
                        gray3 = gray.copy() if 'gray' in locals() else (cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image)
                        enlarged3 = cv2.resize(gray3, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
                        
                        # 頂帽變換去除背景
                        kernel_tophat = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
                        tophat = cv2.morphologyEx(enlarged3, cv2.MORPH_TOPHAT, kernel_tophat)
                        blackhat = cv2.morphologyEx(enlarged3, cv2.MORPH_BLACKHAT, kernel_tophat)
                        processed = cv2.add(enlarged3, tophat)
                        processed = cv2.subtract(processed, blackhat)
                        
                        # 嘗試多個固定閾值並融合
                        for thresh_val in [110, 127, 145, 90]:
                            _, fixed_binary = cv2.threshold(processed, thresh_val, 255, cv2.THRESH_BINARY)
                            
                            # 強力降噪
                            denoised = cv2.fastNlMeansDenoising(fixed_binary, None, 15, 7, 21)
                            
                            # 反色
                            if cv2.mean(denoised)[0] > 127:
                                denoised = cv2.bitwise_not(denoised)
                            
                            # 只用最佳 PSM
                            config = '--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                            result = pytesseract.image_to_string(denoised, config=config).strip()
                            if result:
                                all_results.append((''.join(filter(str.isalnum, result)), f'策略3-閾值{thresh_val}'))
                    except:
                        pass
                    
                    # 策略 4: Canny 邊緣檢測 + 骨架化 (字符輪廓提取)
                    try:
                        gray4 = gray.copy() if 'gray' in locals() else (cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image)
                        enlarged4 = cv2.resize(gray4, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC)
                        
                        # 先降噪
                        denoised4 = cv2.fastNlMeansDenoising(enlarged4, None, 20, 7, 21)
                        
                        # Canny 邊緣檢測
                        blurred4 = cv2.GaussianBlur(denoised4, (5, 5), 0)
                        edges = cv2.Canny(blurred4, 50, 150)
                        
                        # 膨脹連接斷裂邊緣
                        kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                        dilated = cv2.dilate(edges, kernel_dilate, iterations=1)
                        
                        # 超強銳化
                        kernel_sharpen = np.array([[-1,-1,-1,-1,-1],
                                                   [-1, 2, 2, 2,-1],
                                                   [-1, 2, 9, 2,-1],
                                                   [-1, 2, 2, 2,-1],
                                                   [-1,-1,-1,-1,-1]]) / 8.0
                        sharpened = cv2.filter2D(dilated, -1, kernel_sharpen)
                        
                        # Otsu 二值化
                        _, sharp_binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                        
                        # 反色
                        if cv2.mean(sharp_binary)[0] > 127:
                            sharp_binary = cv2.bitwise_not(sharp_binary)
                        
                        # 多種 PSM 和字符集
                        for psm in [6, 7, 8]:
                            config = f'--psm {psm} --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                            result = pytesseract.image_to_string(sharp_binary, config=config).strip()
                            if result:
                                all_results.append((''.join(filter(str.isalnum, result)), f'策略4-邊緣-PSM{psm}'))
                    except:
                        pass
                    
                    # 策略 5: 形態學重建 + 距離變換 (76N8 專用)
                    try:
                        gray5 = gray.copy() if 'gray' in locals() else (cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image)
                        
                        # 超大放大倍率
                        enlarged5 = cv2.resize(gray5, None, fx=8, fy=8, interpolation=cv2.INTER_CUBIC)
                        
                        # 三次非局部均值降噪
                        temp = cv2.fastNlMeansDenoising(enlarged5, None, h=25, templateWindowSize=7, searchWindowSize=21)
                        temp = cv2.fastNlMeansDenoising(temp, None, h=20, templateWindowSize=7, searchWindowSize=21)
                        temp = cv2.fastNlMeansDenoising(temp, None, h=15, templateWindowSize=7, searchWindowSize=21)
                        
                        # 形態學梯度提取字符邊緣
                        kernel_grad = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                        gradient = cv2.morphologyEx(temp, cv2.MORPH_GRADIENT, kernel_grad)
                        
                        # 組合原圖和梯度
                        combined = cv2.addWeighted(temp, 0.7, gradient, 0.3, 0)
                        
                        # 距離變換 + Otsu
                        _, markers = cv2.threshold(combined, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                        
                        # 形態學開閉運算組合
                        kernel_final = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                        opened = cv2.morphologyEx(markers, cv2.MORPH_OPEN, kernel_final, iterations=2)
                        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_final, iterations=1)
                        
                        # 銳化
                        kernel_sharp5 = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
                        final = cv2.filter2D(closed, -1, kernel_sharp5)
                        
                        # 智能反色
                        if cv2.mean(final)[0] > 127:
                            final = cv2.bitwise_not(final)
                        
                        # 嘗試所有可能的 PSM
                        for psm in [6, 7, 8, 10, 11, 13]:
                            config = f'--psm {psm} --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                            result = pytesseract.image_to_string(final, config=config).strip()
                            if result:
                                all_results.append((''.join(filter(str.isalnum, result)), f'策略5-重建-PSM{psm}'))
                    except:
                        pass
                    
                    # ====== 結果分析與選擇 ======
                    if all_results:
                        # 過濾掉太短的結果 (< 3 字符)
                        valid_results = [(r, s) for r, s in all_results if len(r) >= 3]
                        
                        if valid_results:
                            # 統計出現次數,選最常出現的
                            from collections import Counter
                            result_counts = Counter([r for r, _ in valid_results])
                            
                            # 如果有高頻結果 (出現 2 次以上),選它
                            most_common = result_counts.most_common(1)[0]
                            if most_common[1] >= 2:
                                text = most_common[0]
                            else:
                                # 否則選最長的
                                text = max(valid_results, key=lambda x: len(x[0]))[0]
                            
                            # 在日誌中顯示所有嘗試結果 (除錯用)
                            debug_info = "\n".join([f"  {s}: {r}" for r, s in all_results if r])
                            print(f"🔍 Tesseract 嘗試:\n{debug_info}\n✅ 最終選擇: {text}")
                        else:
                            text = ""
                    else:
                        text = ""
                    
                    # 清理結果
                    result = ''.join(filter(str.isalnum, text))
                    
                    if result:
                        # ✅ 使用 after() 在主線程中更新 UI
                        self.after(0, lambda r=result: self.captcha_result_var.set(r))
                        self.after(0, lambda r=result: self.status_label.config(
                            text=f"✅ Tesseract 識別成功: {r}",
                            bg="#e8f5e9",
                            fg="#2e7d32"
                        ))
                    else:
                        self.after(0, lambda: self.captcha_result_var.set("(無法識別)"))
                        self.after(0, lambda: self.status_label.config(
                            text="⚠️ 未能識別驗證碼",
                            bg="#fff3e0",
                            fg="#e65100"
                        ))
                else:
                    # 沒有安裝 pytesseract，使用簡單的模板匹配
                    self.after(0, lambda: messagebox.showinfo(
                        "需要安裝套件",
                        "驗證碼識別需要 Tesseract OCR\n\n"
                        "安裝步驟:\n"
                        "1. pip install pytesseract\n"
                        "2. 下載安裝 Tesseract-OCR:\n"
                        "   https://github.com/tesseract-ocr/tesseract\n"
                        "3. 將 Tesseract 安裝路徑加入系統環境變數"
                    ))
                    self.after(0, lambda: self.status_label.config(
                        text="❌ 缺少 pytesseract 套件",
                        bg="#ffebee",
                        fg="#c62828"
                    ))
                    
            except Exception as e:
                error_msg = str(e)
                # ✅ 使用 after() 在主線程中更新 UI
                self.after(0, lambda: self.captcha_result_var.set("(識別失敗)"))
                self.after(0, lambda: self.status_label.config(
                    text=f"❌ 識別失敗: {error_msg}",
                    bg="#ffebee",
                    fg="#c62828"
                ))
                
                # 如果是 tesseract 路徑問題
                if "tesseract" in error_msg.lower():
                    self.after(0, lambda: messagebox.showerror(
                        "Tesseract 未設定",
                        "無法找到 Tesseract 執行檔\n\n"
                        "請確認:\n"
                        "1. 已安裝 Tesseract-OCR\n"
                        "2. 已將安裝路徑加入環境變數\n"
                        "   或在程式中設定:\n"
                        "   pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'"
                    ))
        
        # 啟動識別線程
        threading.Thread(target=run_recognition, daemon=True).start()


# 測試用
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    manager = ImageManager()
    root.mainloop()
