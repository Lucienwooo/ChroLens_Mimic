"""
腳本管理器 - Script Manager
負責腳本的載入、儲存、重新命名、刪除等操作
"""

import os
import json
import time

# 嘗試匯入 script_io 函式
try:
    from script_io import sio_auto_save_script, sio_load_script, sio_save_script_settings
except ImportError:
    # Fallback 實作
    def sio_auto_save_script(script_dir, events, settings):
        if not os.path.exists(script_dir):
            os.makedirs(script_dir)
        fname = f"autosave_{int(time.time())}.json"
        path = os.path.join(script_dir, fname)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"events": events, "settings": settings}, f, ensure_ascii=False, indent=2)
            return fname
        except Exception as ex:
            print(f"autosave failed: {ex}")
            return ""

    def sio_load_script(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {"events": data.get("events", []), "settings": data.get("settings", {})}
        except Exception as ex:
            print(f"load_script failed: {ex}")
            return {"events": [], "settings": {}}

    def sio_save_script_settings(path, settings):
        try:
            data = {}
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["settings"] = settings
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as ex:
            print(f"save_script_settings failed: {ex}")


class ScriptManager:
    """腳本管理器類別"""
    
    LAST_SCRIPT_FILE = "last_script.txt"
    
    def __init__(self, script_dir, logger=None):
        """
        初始化腳本管理器
        
        Args:
            script_dir: 腳本資料夾路徑
            logger: 日誌函式（可選）
        """
        self.script_dir = script_dir
        self.logger = logger or self._default_logger
        self.current_script = None
        
        # 確保腳本資料夾存在
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)
    
    def _default_logger(self, msg):
        """預設日誌函式"""
        print(msg)
    
    def auto_save(self, events, settings):
        """
        自動儲存腳本
        
        Args:
            events: 事件列表
            settings: 設定字典
            
        Returns:
            腳本檔名
        """
        try:
            filename = sio_auto_save_script(self.script_dir, events, settings)
            self.current_script = filename
            self.logger(f"自動存檔：{filename}，事件數：{len(events)}")
            
            # 儲存為最後一次使用的腳本
            self.save_last_script(filename)
            
            return filename
        except Exception as ex:
            self.logger(f"存檔失敗: {ex}")
            return None
    
    def save_settings(self, script_name, settings):
        """
        儲存腳本設定
        
        Args:
            script_name: 腳本檔名
            settings: 設定字典
            
        Returns:
            是否成功
        """
        if not script_name:
            self.logger("請先選擇一個腳本再儲存設定。")
            return False
        
        path = os.path.join(self.script_dir, script_name)
        if not os.path.exists(path):
            self.logger("找不到腳本檔案，請先錄製或載入腳本。")
            return False
        
        try:
            sio_save_script_settings(path, settings)
            self.logger(f"已將設定儲存到腳本：{script_name}")
            self.logger("【腳本設定已更新】提示：快捷鍵將使用這些參數回放")
            return True
        except Exception as ex:
            self.logger(f"儲存腳本設定失敗: {ex}")
            return False
    
    def load(self, script_name):
        """
        載入腳本
        
        Args:
            script_name: 腳本檔名
            
        Returns:
            包含 events 和 settings 的字典，失敗返回 None
        """
        if not script_name:
            return None
        
        path = os.path.join(self.script_dir, script_name)
        if not os.path.exists(path):
            self.logger(f"找不到腳本檔案：{script_name}")
            return None
        
        try:
            data = sio_load_script(path)
            self.current_script = script_name
            self.logger(f"已載入腳本：{script_name}，事件數：{len(data.get('events', []))}")
            
            # 儲存為最後一次使用的腳本
            self.save_last_script(script_name)
            
            return data
        except Exception as ex:
            self.logger(f"載入腳本失敗: {ex}")
            return None
    
    def rename(self, old_name, new_name):
        """
        重新命名腳本
        
        Args:
            old_name: 舊檔名
            new_name: 新檔名
            
        Returns:
            是否成功
        """
        if not old_name or not new_name:
            self.logger("請輸入有效的腳本名稱。")
            return False
        
        # 確保新檔名有 .json 副檔名
        if not new_name.endswith(".json"):
            new_name += ".json"
        
        old_path = os.path.join(self.script_dir, old_name)
        new_path = os.path.join(self.script_dir, new_name)
        
        if not os.path.exists(old_path):
            self.logger(f"找不到腳本：{old_name}")
            return False
        
        if os.path.exists(new_path):
            self.logger(f"腳本名稱已存在：{new_name}")
            return False
        
        try:
            os.rename(old_path, new_path)
            self.logger(f"已將腳本 {old_name} 重新命名為 {new_name}")
            
            # 更新當前腳本名稱
            if self.current_script == old_name:
                self.current_script = new_name
            
            return True
        except Exception as ex:
            self.logger(f"重新命名失敗: {ex}")
            return False
    
    def delete(self, script_name):
        """
        刪除腳本
        
        Args:
            script_name: 腳本檔名
            
        Returns:
            是否成功
        """
        if not script_name:
            self.logger("請先選擇要刪除的腳本。")
            return False
        
        path = os.path.join(self.script_dir, script_name)
        
        try:
            os.remove(path)
            self.logger(f"已刪除腳本：{script_name}")
            
            # 清除當前腳本
            if self.current_script == script_name:
                self.current_script = None
            
            return True
        except Exception as ex:
            self.logger(f"刪除腳本失敗: {ex}")
            return False
    
    def get_all_scripts(self):
        """
        獲取所有腳本列表
        
        Returns:
            腳本檔名列表
        """
        if not os.path.exists(self.script_dir):
            return []
        
        try:
            scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
            scripts.sort(reverse=True)  # 最新的在前
            return scripts
        except Exception as ex:
            self.logger(f"讀取腳本列表失敗: {ex}")
            return []
    
    def get_script_info(self, script_name):
        """
        獲取腳本資訊
        
        Args:
            script_name: 腳本檔名
            
        Returns:
            包含腳本資訊的字典
        """
        path = os.path.join(self.script_dir, script_name)
        
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            return {
                "name": script_name,
                "events_count": len(data.get("events", [])),
                "settings": data.get("settings", {}),
                "hotkey": data.get("script_hotkey", ""),
                "size": os.path.getsize(path),
                "modified_time": os.path.getmtime(path)
            }
        except Exception as ex:
            self.logger(f"讀取腳本資訊失敗: {ex}")
            return None
    
    def save_last_script(self, script_name):
        """
        儲存最後使用的腳本名稱
        
        Args:
            script_name: 腳本檔名
        """
        try:
            with open(self.LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(script_name)
        except Exception as ex:
            self.logger(f"儲存最後腳本失敗: {ex}")
    
    def load_last_script(self):
        """
        載入最後使用的腳本
        
        Returns:
            腳本資料，失敗返回 None
        """
        try:
            if os.path.exists(self.LAST_SCRIPT_FILE):
                with open(self.LAST_SCRIPT_FILE, "r", encoding="utf-8") as f:
                    script_name = f.read().strip()
                
                if script_name:
                    return self.load(script_name)
        except Exception as ex:
            self.logger(f"載入最後腳本失敗: {ex}")
        
        return None
    
    def get_script_path(self, script_name):
        """
        獲取腳本完整路徑
        
        Args:
            script_name: 腳本檔名
            
        Returns:
            完整路徑
        """
        return os.path.join(self.script_dir, script_name)
