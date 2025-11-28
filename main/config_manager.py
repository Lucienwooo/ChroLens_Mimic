"""
ConfigManager - 單例模式配置管理器
負責統一管理 user_config.json 的讀寫與預設值

使用方式:
    config = ConfigManager.get_instance()
    value = config.get("key", default_value)
    config.set("key", value)
    config.save()
"""

import json
import os
import threading
from typing import Any, Dict

class ConfigManager:
    """單例模式的配置管理器
    
    功能：
    - 統一管理 user_config.json
    - 提供執行緒安全的讀寫
    - 自動處理預設值與向下相容
    - 支援配置遷移 (Migration)
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # 預設配置（包含所有可能的鍵值）
    DEFAULT_CONFIG = {
        "skin": "darkly",
        "last_script": "",
        "repeat": "1",
        "speed": "100",
        "script_dir": "scripts",
        "language": "繁體中文",
        "first_run": True,
        "auto_mini_mode": False,
        "hotkey_map": {
            "start": "F10",
            "pause": "F11",
            "stop": "F9",
            "play": "F12",
            "mini": "alt+`",
            "force_quit": "ctrl+alt+z"
        }
    }
    
    def __init__(self, config_file: str = "user_config.json"):
        """私有建構子，請使用 get_instance() 取得實例"""
        if ConfigManager._instance is not None:
            raise RuntimeError("請使用 ConfigManager.get_instance() 取得實例")
        
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self._load()
    
    @classmethod
    def get_instance(cls, config_file: str = "user_config.json") -> 'ConfigManager':
        """取得 ConfigManager 的單例實例（執行緒安全）"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-checked locking
                    cls._instance = cls(config_file)
        return cls._instance
    
    def _load(self) -> None:
        """從檔案載入配置，若檔案不存在則使用預設值"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # 合併預設值（確保所有鍵都存在）
                    self._config = self._migrate_config(loaded)
            except Exception as e:
                print(f"⚠️ 載入配置失敗，使用預設值: {e}")
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            # 首次執行，使用預設值
            self._config = self.DEFAULT_CONFIG.copy()
            self.save()  # 立即儲存預設配置
    
    def _migrate_config(self, loaded: Dict[str, Any]) -> Dict[str, Any]:
        """配置遷移：確保舊版配置相容新版本
        
        遷移規則：
        1. 補充缺失的鍵（使用預設值）
        2. 移除廢棄的鍵（可選，目前保留所有舊鍵）
        3. 型別轉換與修正
        """
        migrated = self.DEFAULT_CONFIG.copy()
        
        # 更新載入的值（保留舊有設定）
        for key, value in loaded.items():
            if key in migrated:
                # 特殊處理：hotkey_map 需要合併
                if key == "hotkey_map" and isinstance(value, dict):
                    default_hotkeys = self.DEFAULT_CONFIG["hotkey_map"]
                    merged_hotkeys = default_hotkeys.copy()
                    merged_hotkeys.update(value)
                    migrated[key] = merged_hotkeys
                else:
                    migrated[key] = value
            else:
                # 保留未知鍵（向下相容）
                migrated[key] = value
        
        return migrated
    
    def get(self, key: str, default: Any = None) -> Any:
        """取得配置值（執行緒安全）
        
        Args:
            key: 配置鍵名
            default: 若鍵不存在時的預設值
            
        Returns:
            配置值或預設值
        """
        with self._lock:
            return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """設定配置值（執行緒安全）
        
        Args:
            key: 配置鍵名
            value: 配置值
        """
        with self._lock:
            self._config[key] = value
    
    def save(self) -> bool:
        """儲存配置到檔案（執行緒安全，帶重試機制）
        
        Returns:
            是否儲存成功
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self._lock:
                    # 使用臨時檔案寫入，避免寫入失敗導致原檔案損毀
                    temp_file = self.config_file + ".tmp"
                    with open(temp_file, "w", encoding="utf-8") as f:
                        json.dump(self._config, f, ensure_ascii=False, indent=2)
                        f.flush()
                        os.fsync(f.fileno())  # 強制寫入磁碟
                    
                    # 替換原檔案
                    if os.path.exists(self.config_file):
                        os.remove(self.config_file)
                    os.rename(temp_file, self.config_file)
                    return True
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"❌ 儲存配置失敗（重試 {max_retries} 次後）: {e}")
                    # 清理臨時檔案
                    temp_file = self.config_file + ".tmp"
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    return False
                import time
                time.sleep(0.1)  # 等待後重試
        
        return False
    
    def get_all(self) -> Dict[str, Any]:
        """取得所有配置（返回副本，避免外部修改）
        
        Returns:
            配置的副本
        """
        with self._lock:
            return self._config.copy()
    
    def update(self, updates: Dict[str, Any]) -> None:
        """批次更新配置（執行緒安全）
        
        Args:
            updates: 要更新的鍵值對字典
        """
        with self._lock:
            self._config.update(updates)
    
    def reset_to_default(self) -> None:
        """重置為預設配置"""
        with self._lock:
            self._config = self.DEFAULT_CONFIG.copy()
        self.save()


# 提供便利函式（向下相容舊代碼）
def load_user_config() -> Dict[str, Any]:
    """載入使用者配置（向下相容函式）
    
    注意：建議新代碼直接使用 ConfigManager.get_instance()
    """
    return ConfigManager.get_instance().get_all()


def save_user_config(config: Dict[str, Any]) -> None:
    """儲存使用者配置（向下相容函式）
    
    注意：建議新代碼直接使用 ConfigManager.get_instance()
    """
    manager = ConfigManager.get_instance()
    manager.update(config)
    manager.save()


# ====== 使用範例 ======
if __name__ == "__main__":
    # 取得單例實例
    config = ConfigManager.get_instance()
    
    # 讀取配置
    skin = config.get("skin", "darkly")
    print(f"當前主題: {skin}")
    
    # 設定配置
    config.set("skin", "solar")
    config.save()
    
    # 批次更新
    config.update({
        "language": "English",
        "speed": "150"
    })
    config.save()
    
    # 取得所有配置
    all_config = config.get_all()
    print(f"所有配置: {all_config}")
