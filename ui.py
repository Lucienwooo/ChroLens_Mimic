import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import font
from tooltip import Tooltip
import os

class RecorderUI(tb.Window):
    def __init__(self, controller):
        # 儲存 controller 參考以便回調
        self.controller = controller
        
        # 從 controller 取得設定
        self.user_config = controller.user_config
        skin = self.user_config.get("skin", "darkly")
        lang = self.user_config.get("language", "繁體中文")
        
        # 初始化主視窗
        super().__init__(themename=skin)
        self.title("ChroLens_Mimic_2.6")
        self.geometry("900x550")
        self.resizable(True, True)
        
        # 設定 icon
        try:
            import sys
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "umi_奶茶色.ico")
            else:
                icon_path = "umi_奶茶色.ico"
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"無法設定 icon: {e}")
        
        # 初始化樣式
        self._setup_styles()
        
        # 建立 UI 元件 - 依正確順序建立
        self._create_frames()  # 先建立所需的 frames
        self._create_page_menu()  # 建立 page_menu
        self._create_top_buttons()
        self._create_control_panel()
        self._create_script_panel()
        self._create_log_panel()
        
        # 最後再設定初始頁面
        self.page_menu.selection_set(0)
        self.show_page(0)

    def _create_frames(self):
        """建立主要框架"""
        # 頁面區域
        self.frm_page = tb.Frame(self, padding=(10, 0, 10, 10))
        self.frm_page.pack(fill="both", expand=True)
        self.frm_page.grid_rowconfigure(0, weight=1)
        self.frm_page.grid_columnconfigure(1, weight=1)

    def _create_page_menu(self):
        """建立頁面選單"""
        self.page_menu = tk.Listbox(self.frm_page, width=18, font=("LINESeedTW_TTF_Rg", 9), height=5)
        self.page_menu.insert(0, "1.日誌顯示")
        self.page_menu.insert(1, "2.腳本設定")
        self.page_menu.insert(2, "3.整體設定")
        self.page_menu.grid(row=0, column=0, sticky="ns", padx=(0, 8), pady=4)
        self.page_menu.bind("<<ListboxSelect>>", self.on_page_selected)
        
    def _setup_styles(self):
        """設定所有 ttk 樣式"""
        self.style.configure("My.TButton", font=("LINESeedTW_TTF_Rg", 9))
        self.style.configure("My.TLabel", font=("LINESeedTW_TTF_Rg", 9))
        self.style.configure("My.TEntry", font=("LINESeedTW_TTF_Rg", 9))
        self.style.configure("My.TCombobox", font=("LINESeedTW_TTF_Rg", 9))
        self.style.configure("My.TCheckbutton", font=("LINESeedTW_TTF_Rg", 9))
        self.style.configure("miniBold.TButton", font=("LINESeedTW_TTF_Bd", 9, "bold"))

    def _create_top_buttons(self):
        """建立頂部按鈕區域"""
        frm_top = tb.Frame(self, padding=(8, 10, 8, 5))
        frm_top.pack(fill="x")

        self.btn_start = tb.Button(frm_top, text="開始錄製", command=self.controller.start_record,
                                 bootstyle=PRIMARY, width=14, style="My.TButton")
        self.btn_start.grid(row=0, column=0, padx=(0, 4))
        # ... 其他按鈕程式碼 ...

    def _create_control_panel(self):
        """建立控制面板"""
        # ... 控制面板程式碼 ...

    def _create_script_panel(self):
        """建立腳本面板"""
        # ... 腳本面板程式碼 ...

    def _create_log_panel(self):
        """建立日誌面板"""
        # ... 日誌面板程式碼 ...

    def _create_pages(self):
        """建立頁面"""
        # ... 頁面建立程式碼 ...

    def show_page(self, idx):
        """切換顯示頁面"""
        # ... 頁面切換程式碼 ...