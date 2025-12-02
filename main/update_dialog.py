"""
更新對話框 UI
提供使用者友善的更新介面

作者: Lucien
版本: 1.0.0
日期: 2025/11/12
"""

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
import threading
import os
import sys


def get_icon_path():
    """取得圖示檔案路徑（打包後和開發環境通用）"""
    try:
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, "umi_奶茶色.ico")
        else:
            if os.path.exists("umi_奶茶色.ico"):
                return "umi_奶茶色.ico"
            elif os.path.exists("../pic/umi_奶茶色.ico"):
                return "../pic/umi_奶茶色.ico"
            elif os.path.exists("../umi_奶茶色.ico"):
                return "../umi_奶茶色.ico"
            else:
                return "umi_奶茶色.ico"
    except:
        return "umi_奶茶色.ico"
import os
import sys


def get_icon_path():
    """取得圖示檔案路徑（打包後和開發環境通用）"""
    try:
        if getattr(sys, 'frozen', False):
            # 打包後的環境
            return os.path.join(sys._MEIPASS, "umi_奶茶色.ico")
        else:
            # 開發環境
            if os.path.exists("umi_奶茶色.ico"):
                return "umi_奶茶色.ico"
            elif os.path.exists("../pic/umi_奶茶色.ico"):
                return "../pic/umi_奶茶色.ico"
            elif os.path.exists("../umi_奶茶色.ico"):
                return "../umi_奶茶色.ico"
            else:
                return "umi_奶茶色.ico"
    except:
        return "umi_奶茶色.ico"


class UpdateDialog:
    """更新對話框"""
    
    def __init__(self, parent, update_manager, update_info):
        """
        初始化更新對話框
        
        Args:
            parent: 父視窗
            update_manager: UpdateManager 實例
            update_info: 更新資訊字典
        """
        self.parent = parent
        self.update_manager = update_manager
        self.update_info = update_info
        
        self.dialog = None
        self.downloading = False
        self.user_confirmed = False
        
        # 建立對話框
        self._create_info_dialog()
    
    def _create_info_dialog(self):
        """建立資訊對話框（顯示版本與更新內容）"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("發現新版本")
        
        # 調整視窗大小：寬度減少 1/3 (從 600 → 400)，高度減少 1/2 (從 500 → 250)
        width = 450
        height = 380
        
        self.dialog.geometry(f"{width}x{height}")
        self.dialog.minsize(400, 350)  # 設定最小尺寸
        self.dialog.resizable(True, True)  # 允許調整大小
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 置中顯示
        self.dialog.update_idletasks()
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # 設定視窗圖標
        try:
            icon_path = get_icon_path()
            if os.path.exists(icon_path):
                self.dialog.iconbitmap(icon_path)
        except:
            pass
        
        # === 標題區 ===
        title_frame = tb.Frame(self.dialog, bootstyle=SUCCESS)
        title_frame.pack(fill=X, padx=0, pady=0)
        
        title_label = tb.Label(
            title_frame,
            text="🎉 發現新版本！",
            font=("Microsoft JhengHei", 14, "bold"),
            bootstyle=SUCCESS
        )
        title_label.pack(pady=15)
        
        # === 版本資訊區 ===
        info_frame = tb.Frame(self.dialog, padding=15)
        info_frame.pack(fill=BOTH, expand=True)
        
        # 當前版本
        current_label = tb.Label(
            info_frame,
            text=f"目前版本：{self.update_manager.current_version}",
            font=("Microsoft JhengHei", 11)
        )
        current_label.pack(anchor=W, pady=(0, 5))
        
        # 最新版本
        latest_label = tb.Label(
            info_frame,
            text=f"最新版本：{self.update_info['version']}",
            font=("Microsoft JhengHei", 11, "bold"),
            bootstyle=SUCCESS
        )
        latest_label.pack(anchor=W, pady=(0, 15))
        
        # 更新內容標題與按鈕區域（同一行）
        header_frame = tb.Frame(info_frame)
        header_frame.pack(fill=X, pady=(0, 5))
        
        notes_label = tb.Label(
            header_frame,
            text="更新內容：",
            font=("Microsoft JhengHei", 10, "bold")
        )
        notes_label.pack(side=LEFT)
        
        # 按鈕組（放在右上角）
        button_group = tb.Frame(header_frame)
        button_group.pack(side=RIGHT)
        
        # 檢查是否有下載連結
        if not self.update_info.get('download_url'):
            # 沒有下載連結，只能手動下載
            manual_btn = tb.Button(
                button_group,
                text="前往 GitHub",
                command=self._open_github,
                bootstyle=SUCCESS,
                width=12
            )
            manual_btn.pack(side=LEFT, padx=(0, 5))
        else:
            # 有下載連結，可以自動更新
            update_btn = tb.Button(
                button_group,
                text="立即更新",
                command=self._start_update,
                bootstyle=SUCCESS,
                width=10
            )
            update_btn.pack(side=LEFT, padx=(0, 5))
        
        cancel_btn = tb.Button(
            button_group,
            text="關閉",
            command=self._cancel,
            bootstyle=SECONDARY,
            width=8
        )
        cancel_btn.pack(side=LEFT)
        
        # 更新內容文字框（可滾動）
        notes_frame = tb.Frame(info_frame)
        notes_frame.pack(fill=BOTH, expand=True, pady=(0, 0))
        
        scrollbar = tb.Scrollbar(notes_frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.notes_text = tk.Text(
            notes_frame,
            wrap=tk.WORD,
            font=("Microsoft JhengHei", 9),
            yscrollcommand=scrollbar.set,
            relief=SOLID,
            borderwidth=1,
            padx=10,
            pady=10
        )
        self.notes_text.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self.notes_text.yview)
        
        # 插入更新內容
        release_notes = self.update_info['notes']
        if not release_notes or release_notes == '無更新說明':
            release_notes = "本次更新包含功能改進與錯誤修復。"
        
        self.notes_text.insert('1.0', release_notes)
        self.notes_text.config(state='disabled')
        
        # 綁定關閉事件
        self.dialog.protocol("WM_DELETE_WINDOW", self._cancel)
    
    def _open_github(self):
        """開啟 GitHub 頁面"""
        import webbrowser
        release_url = f"https://github.com/{self.update_manager.GITHUB_REPO}/releases/latest"
        webbrowser.open(release_url)
        self.dialog.destroy()
    
    def _start_update(self):
        """開始更新流程"""
        self.user_confirmed = True
        
        # 轉換為進度對話框
        self._switch_to_progress_dialog()
        
        # 設定回調
        self.update_manager.set_progress_callback(self._on_progress)
        self.update_manager.set_complete_callback(self._on_complete)
        self.update_manager.set_error_callback(self._on_error)
        
        # 開始下載與安裝
        self.update_manager.download_and_install()
    
    def _switch_to_progress_dialog(self):
        """切換為進度對話框"""
        # 清空對話框
        for widget in self.dialog.winfo_children():
            widget.destroy()
        
        self.dialog.title("正在更新")
        
        # 調整視窗大小為進度模式（較小但仍可見）
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        width = 550
        height = 300
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        self.dialog.minsize(500, 250)
        
        # === 標題 ===
        title_label = tb.Label(
            self.dialog,
            text="正在下載更新...",
            font=("Microsoft JhengHei", 12, "bold")
        )
        title_label.pack(pady=(30, 15))
        
        # === 進度條 ===
        progress_frame = tb.Frame(self.dialog)
        progress_frame.pack(fill=X, padx=40, pady=15)
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = tb.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=450,
            bootstyle=SUCCESS
        )
        self.progress_bar.pack(fill=X, expand=True)
        
        # === 狀態標籤 ===
        self.status_label = tb.Label(
            self.dialog,
            text="準備中...",
            font=("Microsoft JhengHei", 10)
        )
        self.status_label.pack(pady=(10, 5))
        
        # === 進度百分比 ===
        self.percent_label = tb.Label(
            self.dialog,
            text="0%",
            font=("Consolas", 14, "bold"),
            bootstyle=INFO
        )
        self.percent_label.pack(pady=(5, 30))
        
        # 禁用關閉按鈕
        self.dialog.protocol("WM_DELETE_WINDOW", lambda: None)
    
    def _on_progress(self, progress: float, message: str):
        """進度回調"""
        # 在主執行緒更新 UI
        self.dialog.after(0, self._update_progress_ui, progress, message)
    
    def _update_progress_ui(self, progress: float, message: str):
        """更新進度 UI（在主執行緒）"""
        self.progress_var.set(progress)
        self.status_label.config(text=message)
        self.percent_label.config(text=f"{progress:.0f}%")
    
    def _on_complete(self):
        """完成回調"""
        # 在主執行緒顯示完成對話框
        self.dialog.after(0, self._show_complete_dialog)
    
    def _show_complete_dialog(self):
        """顯示完成對話框"""
        result = messagebox.askyesno(
            "更新完成",
            "更新已準備完成！\n\n程式需要重新啟動以套用更新。\n是否立即重啟？",
            parent=self.dialog
        )
        
        if result:
            # 使用者選擇立即重啟
            self._restart_app()
        else:
            # 使用者選擇稍後重啟
            messagebox.showinfo(
                "提示",
                "更新將在下次啟動程式時生效。",
                parent=self.dialog
            )
            self.dialog.destroy()
    
    def _restart_app(self):
        """重啟應用程式"""
        # 關閉對話框
        self.dialog.destroy()
        
        # 關閉主視窗（這會觸發更新腳本）
        self.parent.quit()
        self.parent.destroy()
    
    def _on_error(self, error: str):
        """錯誤回調"""
        # 在主執行緒顯示錯誤
        self.dialog.after(0, self._show_error, error)
    
    def _show_error(self, error: str):
        """顯示錯誤（在主執行緒）"""
        messagebox.showerror("更新失敗", error, parent=self.dialog)
        self.dialog.destroy()
    
    def _cancel(self):
        """取消更新"""
        if not self.downloading:
            self.dialog.destroy()


class NoUpdateDialog:
    """無更新對話框"""
    
    def __init__(self, parent, current_version):
        """
        初始化無更新對話框
        
        Args:
            parent: 父視窗
            current_version: 當前版本號
        """
        self.parent = parent
        self.current_version = current_version
        
        # 建立對話框
        self._create_dialog()
    
    def _create_dialog(self):
        """建立對話框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("檢查更新")
        
        # 設定較大的視窗尺寸
        width = 400
        height = 250
        self.dialog.geometry(f"{width}x{height}")
        self.dialog.minsize(350, 200)
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 置中顯示
        self.dialog.update_idletasks()
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # 設定視窗圖標
        try:
            icon_path = get_icon_path()
            if os.path.exists(icon_path):
                self.dialog.iconbitmap(icon_path)
        except:
            pass
        
        # === 標題區 ===
        try:
            icon_path = get_icon_path()
            if os.path.exists(icon_path):
                self.dialog.iconbitmap(icon_path)
        except:
            pass
        
        # === 標題區 ===
        icon_label = tb.Label(
            self.dialog,
            text="✓",
            font=("Microsoft JhengHei", 48),
            bootstyle=SUCCESS
        )
        icon_label.pack(pady=(30, 10))
        
        # === 訊息 ===
        message_label = tb.Label(
            self.dialog,
            text="已是最新版本",
            font=("Microsoft JhengHei", 12, "bold")
        )
        message_label.pack(pady=(0, 5))
        
        version_label = tb.Label(
            self.dialog,
            text=f"當前版本：{self.current_version}",
            font=("Microsoft JhengHei", 10)
        )
        version_label.pack(pady=(0, 20))
        
        # === 確定按鈕 ===
        ok_btn = tb.Button(
            self.dialog,
            text="確定",
            command=self.dialog.destroy,
            bootstyle=SUCCESS,
            width=12
        )
        ok_btn.pack()
        
        # 綁定 Enter 鍵
        self.dialog.bind('<Return>', lambda e: self.dialog.destroy())
        self.dialog.protocol("WM_DELETE_WINDOW", self.dialog.destroy)


# ============================================
# 使用示例
# ============================================
if __name__ == "__main__":
    # 測試無更新對話框
    root = tb.Window(themename="darkly")
    root.geometry("400x300")
    
    def test_no_update():
        NoUpdateDialog(root, "2.6.3")
    
    def test_update():
        # 模擬更新資訊
        from update_manager import UpdateManager
        
        update_info = {
            'version': '2.6.4',
            'notes': '''## 新增功能
- 自動更新系統
- 改進的 UI/UX

## 錯誤修復
- 修復快捷鍵問題
- 修復時間顯示問題''',
            'download_url': 'https://example.com/update.zip',
            'asset_name': 'ChroLens_Mimic_v2.6.4.zip',
            'has_update': True
        }
        
        updater = UpdateManager("2.6.3")
        UpdateDialog(root, updater, update_info)
    
    btn1 = tb.Button(root, text="測試：無更新", command=test_no_update, width=20)
    btn1.pack(pady=20)
    
    btn2 = tb.Button(root, text="測試：有更新", command=test_update, width=20)
    btn2.pack(pady=20)
    
    root.mainloop()
