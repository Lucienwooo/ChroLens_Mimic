"""
LoggerHandler - 標準化日誌系統
整合 Python logging 模組與 Tkinter Text Widget

使用方式:
    # 在 RecorderApp 中初始化
    handler = TkTextHandler(self.log_text)
    logger = logging.getLogger("ChroLens")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # 在其他模組使用
    import logging
    logger = logging.getLogger("ChroLens")
    logger.info("這是訊息")
"""

import logging
import tkinter as tk
from datetime import datetime
from typing import Optional
import threading


class TkTextHandler(logging.Handler):
    """將 logging 記錄輸出到 Tkinter Text Widget
    
    特性：
    - 執行緒安全（使用 after() 在主執行緒更新 UI）
    - 自動捲動到最新訊息
    - 支援顏色標記（INFO/WARNING/ERROR）
    - 自動限制行數（防止記憶體溢出）
    """
    
    def __init__(self, text_widget: tk.Text, max_lines: int = 1000):
        """初始化處理器
        
        Args:
            text_widget: Tkinter Text Widget
            max_lines: 最大保留行數（超過會自動刪除舊記錄）
        """
        super().__init__()
        self.text_widget = text_widget
        self.max_lines = max_lines
        self._lock = threading.Lock()
        
        # 配置顏色標記（需在主執行緒中初始化）
        try:
            self.text_widget.tag_configure("INFO", foreground="#00FF00")  # 綠色
            self.text_widget.tag_configure("WARNING", foreground="#FFA500")  # 橙色
            self.text_widget.tag_configure("ERROR", foreground="#FF0000")  # 紅色
            self.text_widget.tag_configure("DEBUG", foreground="#888888")  # 灰色
            self.text_widget.tag_configure("CRITICAL", foreground="#FF00FF")  # 紫紅色
        except Exception:
            pass  # 若在非主執行緒初始化，稍後會自動配置
    
    def emit(self, record: logging.LogRecord) -> None:
        """處理日誌記錄（logging.Handler 的核心方法）
        
        Args:
            record: 日誌記錄物件
        """
        try:
            msg = self.format(record)
            level = record.levelname
            
            # 使用 after() 確保在主執行緒更新 UI
            self.text_widget.after(0, self._append_message, msg, level)
        except Exception:
            self.handleError(record)
    
    def _append_message(self, msg: str, level: str) -> None:
        """在 Text Widget 中追加訊息（必須在主執行緒執行）
        
        Args:
            msg: 訊息內容
            level: 日誌等級（INFO/WARNING/ERROR等）
        """
        try:
            with self._lock:
                # 插入訊息（帶顏色標記）
                self.text_widget.insert(tk.END, msg + "\n", level)
                
                # 自動捲動到最新訊息
                self.text_widget.see(tk.END)
                
                # 限制行數（防止記憶體溢出）
                self._trim_lines()
        except Exception:
            pass  # 靜默失敗，避免影響主程式
    
    def _trim_lines(self) -> None:
        """刪除超過限制的舊記錄"""
        try:
            line_count = int(self.text_widget.index('end-1c').split('.')[0])
            if line_count > self.max_lines:
                # 刪除最舊的記錄
                delete_count = line_count - self.max_lines
                self.text_widget.delete('1.0', f'{delete_count + 1}.0')
        except Exception:
            pass


class LoggerManager:
    """日誌管理器（單例模式）
    
    功能：
    - 統一管理應用程式的日誌系統
    - 支援同時輸出到 UI 和檔案
    - 提供便利的日誌記錄方法
    """
    
    _instance: Optional['LoggerManager'] = None
    _lock = threading.Lock()
    
    def __init__(self, logger_name: str = "ChroLens"):
        """私有建構子，請使用 get_instance()"""
        if LoggerManager._instance is not None:
            raise RuntimeError("請使用 LoggerManager.get_instance() 取得實例")
        
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False  # 避免重複輸出
        
        # 預設格式
        self.formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        
        self.text_handler: Optional[TkTextHandler] = None
        self.file_handler: Optional[logging.FileHandler] = None
    
    @classmethod
    def get_instance(cls, logger_name: str = "ChroLens") -> 'LoggerManager':
        """取得 LoggerManager 的單例實例（執行緒安全）"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(logger_name)
        return cls._instance
    
    def setup_text_handler(self, text_widget: tk.Text, max_lines: int = 1000) -> None:
        """設定 Text Widget 輸出
        
        Args:
            text_widget: Tkinter Text Widget
            max_lines: 最大保留行數
        """
        if self.text_handler:
            self.logger.removeHandler(self.text_handler)
        
        self.text_handler = TkTextHandler(text_widget, max_lines)
        self.text_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.text_handler)
    
    def setup_file_handler(self, log_file: str = "debug.log", mode: str = 'a') -> None:
        """設定檔案輸出
        
        Args:
            log_file: 日誌檔案路徑
            mode: 檔案模式（'a' = 追加, 'w' = 覆寫）
        """
        if self.file_handler:
            self.logger.removeHandler(self.file_handler)
        
            try:
                self.file_handler = logging.FileHandler(log_file, mode=mode, encoding='utf-8')
                self.file_handler.setFormatter(self.formatter)
                self.logger.addHandler(self.file_handler)
            except Exception as e:
                print(f"警告: 無法創建日誌檔案: {e}")    def info(self, msg: str) -> None:
        """記錄 INFO 訊息"""
        self.logger.info(msg)
    
    def warning(self, msg: str) -> None:
        """記錄 WARNING 訊息"""
        self.logger.warning(msg)
    
    def error(self, msg: str, exc_info: bool = False) -> None:
        """記錄 ERROR 訊息
        
        Args:
            msg: 錯誤訊息
            exc_info: 是否包含例外堆疊（True = 顯示完整錯誤）
        """
        self.logger.error(msg, exc_info=exc_info)
    
    def debug(self, msg: str) -> None:
        """記錄 DEBUG 訊息"""
        self.logger.debug(msg)
    
    def critical(self, msg: str) -> None:
        """記錄 CRITICAL 訊息"""
        self.logger.critical(msg)
    
    def set_level(self, level: int) -> None:
        """設定日誌等級
        
        Args:
            level: logging.DEBUG / INFO / WARNING / ERROR / CRITICAL
        """
        self.logger.setLevel(level)
    
    def get_logger(self) -> logging.Logger:
        """取得原始 Logger 物件（進階使用）"""
        return self.logger


# ====== 便利函式（向下相容） ======
def get_logger(name: str = "ChroLens") -> logging.Logger:
    """取得日誌記錄器（便利函式）
    
    使用範例:
        from logger_handler import get_logger
        logger = get_logger()
        logger.info("這是訊息")
    """
    return LoggerManager.get_instance(name).get_logger()


# ====== 使用範例 ======
if __name__ == "__main__":
    import tkinter as tk
    import ttkbootstrap as tb
    
    # 創建測試視窗
    root = tb.Window(themename="darkly")
    root.title("LoggerHandler 測試")
    root.geometry("600x400")
    
    # 創建 Text Widget
    text = tk.Text(root, bg="#2b2b2b", fg="#00ff00", font=("Consolas", 10))
    text.pack(fill="both", expand=True, padx=10, pady=10)
    
    # 設定日誌系統
    logger_mgr = LoggerManager.get_instance()
    logger_mgr.setup_text_handler(text)
    logger_mgr.setup_file_handler("test_debug.log")
    
    # 測試按鈕
    def test_logging():
        logger_mgr.info("這是 INFO 訊息")
        logger_mgr.warning("這是 WARNING 訊息")
        logger_mgr.error("這是 ERROR 訊息")
        logger_mgr.debug("這是 DEBUG 訊息")
        logger_mgr.critical("這是 CRITICAL 訊息")
    
    btn = tb.Button(root, text="測試日誌", command=test_logging, bootstyle="success")
    btn.pack(pady=10)
    
    # 顯示歡迎訊息
    logger_mgr.info("日誌系統測試")
    logger_mgr.info("點擊按鈕測試不同等級的日誌訊息")
    
    root.mainloop()
