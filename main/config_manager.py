"""
配置管理器 - Configuration Manager
負責處理所有使用者配置的讀取、儲存和管理
"""

import json
import os

class ConfigManager:
    """配置管理器類別"""
    
    CONFIG_FILE = "user_config.json"
    SCRIPTS_DIR = "scripts"
    
    # 預設配置
    DEFAULT_CONFIG = {
        "skin": "darkly",
        "last_script": "",
        "repeat": "1",
        "speed": "100",
        "script_dir": SCRIPTS_DIR,
        "language": "繁體中文",
        "hotkey_map": {
            "start": "F10",
            "pause": "F11",
                "stop": "F9",
            "play": "F12",
                "mini": "alt+`",
                # 強制關閉（注意: Ctrl+Alt+Delete 無法被應用程式攔截，預設使用 Ctrl+Alt+End）
                "force_quit": "ctrl+alt+end"
        }
    }
    
    def __init__(self):
        """初始化配置管理器"""
        self.config = self.load()
    
    def load(self):
        """載入配置檔案"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                # 合併預設值（確保新增的配置項不會缺失）
                return self._merge_with_defaults(config)
            except Exception as e:
                print(f"載入配置檔案失敗: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            # 首次執行，使用預設配置
            return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        """儲存配置檔案"""
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"儲存配置檔案失敗: {e}")
            return False
    
    def get(self, key, default=None):
        """獲取配置值"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """設定配置值"""
        self.config[key] = value
    
    def update(self, **kwargs):
        """批次更新配置"""
        self.config.update(kwargs)
    
    def reset_to_defaults(self):
        """重置為預設值"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
    
    def _merge_with_defaults(self, config):
        """合併使用者配置與預設配置"""
        merged = self.DEFAULT_CONFIG.copy()
        
        # 遞迴合併巢狀字典（如 hotkey_map）
        for key, value in config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value
        
        return merged
    
    def get_hotkey(self, action):
        """獲取指定動作的快捷鍵"""
        return self.config.get("hotkey_map", {}).get(action, "")
    
    def set_hotkey(self, action, hotkey):
        """設定指定動作的快捷鍵"""
        if "hotkey_map" not in self.config:
            self.config["hotkey_map"] = {}
        self.config["hotkey_map"][action] = hotkey
    
    def get_all_hotkeys(self):
        """獲取所有快捷鍵"""
        return self.config.get("hotkey_map", {})
    
    def ensure_script_dir(self):
        """確保腳本資料夾存在"""
        script_dir = self.config.get("script_dir", self.SCRIPTS_DIR)
        if not os.path.exists(script_dir):
            os.makedirs(script_dir)
        return script_dir


def load_user_config():
    """向後相容的函式 - 載入使用者配置"""
    manager = ConfigManager()
    return manager.config


def save_user_config(config):
    """向後相容的函式 - 儲存使用者配置"""
    try:
        with open(ConfigManager.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"儲存配置失敗: {e}")
