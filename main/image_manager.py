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
        
        self._create_ui()
        self._load_images()
        
        # 置頂顯示
        self.lift()
        self.focus_force()
    
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
        """顯示圖片預覽"""
        try:
            image = Image.open(image_path)
            
            # 縮放以適應預覽區域
            max_size = (400, 300)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # 保持引用
            
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


# 測試用
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    manager = ImageManager()
    root.mainloop()
