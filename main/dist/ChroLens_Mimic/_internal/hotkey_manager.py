"""
快捷鍵管理器 - Hotkey Manager
負責註冊、取消註冊和管理所有快捷鍵

重要更新 (2025/01/12):
- 改用 pynput 模組取代 keyboard 模組
- 解決 PyInstaller 打包後快捷鍵失效問題
- 使用主程式的監聽器系統，不再獨立註冊
"""

import os
import json


class HotkeyManager:
    """快捷鍵管理器類別"""
    
    def __init__(self, app, config_manager, script_manager):
        """
        初始化快捷鍵管理器
        
        Args:
            app: 主應用程式實例（用於回調函式）
            config_manager: 配置管理器實例
            script_manager: 腳本管理器實例
        """
        self.app = app
        self.config = config_manager
        self.script_manager = script_manager
        
        # 快捷鍵處理器字典
        self._system_handlers = {}  # 系統快捷鍵（錄製、停止等）
        self._script_handlers = {}  # 腳本快捷鍵
    
    def register_all(self):
        """
        註冊所有快捷鍵（透過主程式的 pynput 監聽器）
        
        新設計：
        - 不再直接使用 keyboard.add_hotkey()
        - 委託給主程式的 _register_hotkeys() 和 _register_script_hotkeys()
        - 確保與主程式的 pynput 監聽器保持一致
        """
        # 使用主程式的快捷鍵註冊方法
        if hasattr(self.app, '_register_hotkeys'):
            self.app._register_hotkeys()
        if hasattr(self.app, '_register_script_hotkeys'):
            self.app._register_script_hotkeys()
    
    def register_system_hotkeys(self):
        """
        註冊系統快捷鍵（錄製、停止、回放等）
        
        新實現：委託給主程式的 _register_hotkeys()
        """
        if hasattr(self.app, '_register_hotkeys'):
            self.app._register_hotkeys()
        else:
            if hasattr(self.app, 'log'):
                self.app.log("警告：主程式缺少 _register_hotkeys() 方法")
    
    def register_script_hotkeys(self):
        """
        註冊所有腳本快捷鍵
        
        新實現：委託給主程式的 _register_script_hotkeys()
        """
        if hasattr(self.app, '_register_script_hotkeys'):
            self.app._register_script_hotkeys()
        else:
            if hasattr(self.app, 'log'):
                self.app.log("警告：主程式缺少 _register_script_hotkeys() 方法")
    
    def _play_script_by_hotkey(self, script):
        """
        透過快捷鍵觸發腳本回放（使用腳本儲存的參數）
        
        Args:
            script: 腳本檔名
        """
        if self.app.playing or self.app.recording:
            if hasattr(self.app, 'log'):
                self.app.log(f"目前正在錄製或回放中，無法執行腳本：{script}")
            return
        
        # 載入腳本
        data = self.script_manager.load(script)
        if not data:
            return
        
        # 套用腳本的參數設定
        self.app.events = data.get("events", [])
        settings = data.get("settings", {})
        
        # 更新 UI 參數
        self.app.speed_var.set(settings.get("speed", "100"))
        self.app.repeat_var.set(settings.get("repeat", "1"))
        self.app.repeat_time_var.set(settings.get("repeat_time", "00:00:00"))
        self.app.repeat_interval_var.set(settings.get("repeat_interval", "00:00:00"))
        self.app.random_interval_var.set(settings.get("random_interval", False))
        
        # 更新腳本選單顯示
        self.app.script_var.set(script)
        
        if hasattr(self.app, 'log'):
            self.app.log(f"透過快捷鍵載入腳本：{script}")
        
        # 開始回放
        self.app.play_record()
    
    def unregister_all(self):
        """
        取消註冊所有快捷鍵
        
        新實現：停止主程式的 pynput 監聽器
        """
        # 停止主程式的監聽器
        if hasattr(self.app, '_pynput_listener') and self.app._pynput_listener:
            try:
                self.app._pynput_listener.stop()
            except Exception:
                pass
        
        # 清空快捷鍵組合表
        if hasattr(self.app, '_hotkey_combinations'):
            self.app._hotkey_combinations.clear()
        
        self._system_handlers.clear()
        self._script_handlers.clear()
    
    def unregister_system_hotkeys(self):
        """
        取消註冊系統快捷鍵
        
        新實現：清空快捷鍵組合表中的系統快捷鍵
        """
        if hasattr(self.app, '_hotkey_combinations'):
            # 移除非腳本快捷鍵
            to_remove = [k for k, v in self.app._hotkey_combinations.items() 
                        if not v.get("name", "").startswith("script:")]
            for k in to_remove:
                self.app._hotkey_combinations.pop(k, None)
        
        self._system_handlers.clear()
    
    def unregister_script_hotkeys(self):
        """
        取消註冊腳本快捷鍵
        
        新實現：清空快捷鍵組合表中的腳本快捷鍵
        """
        if hasattr(self.app, '_hotkey_combinations'):
            # 移除腳本快捷鍵
            to_remove = [k for k, v in self.app._hotkey_combinations.items() 
                        if v.get("name", "").startswith("script:")]
            for k in to_remove:
                self.app._hotkey_combinations.pop(k, None)
        
        self._script_handlers.clear()
    
    def set_script_hotkey(self, script_name, hotkey):
        """
        為腳本設定快捷鍵
        
        Args:
            script_name: 腳本檔名
            hotkey: 快捷鍵字串
            
        Returns:
            是否成功
        """
        if not script_name or not hotkey or hotkey == "輸入按鍵":
            if hasattr(self.app, 'log'):
                self.app.log("請先選擇腳本並輸入有效的快捷鍵。")
            return False
        
        path = self.script_manager.get_script_path(script_name)
        
        try:
            # 讀取現有資料
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
            
            # 儲存快捷鍵到腳本（可能在 settings 或根層級）
            if "settings" in data:
                data["settings"]["script_hotkey"] = hotkey
            else:
                data["script_hotkey"] = hotkey
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 重新註冊所有腳本的快捷鍵
            self.register_script_hotkeys()
            
            if hasattr(self.app, 'log'):
                self.app.log(f"已設定腳本 {script_name} 的快捷鍵：{hotkey}")
                self.app.log("提示：該快捷鍵將使用腳本內儲存的參數直接回放")
            
            return True
        except Exception as ex:
            if hasattr(self.app, 'log'):
                self.app.log(f"設定腳本快捷鍵失敗: {ex}")
            return False
    
    def get_script_hotkey(self, script_name):
        """
        獲取腳本的快捷鍵
        
        Args:
            script_name: 腳本檔名
            
        Returns:
            快捷鍵字串，若無則返回空字串
        """
        path = self.script_manager.get_script_path(script_name)
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("script_hotkey", "")
        except Exception:
            return ""
    
    def update_labels(self):
        """更新 UI 按鈕上的快捷鍵標籤"""
        hotkey_map = self.config.get_all_hotkeys()
        
        # 更新主視窗按鈕
        if hasattr(self.app, 'btn_start'):
            # 根據語言取得按鈕文字
            lang = self.app.language_var.get() if hasattr(self.app, 'language_var') else "繁體中文"
            
            try:
                from lang import LANG_MAP
                lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
                
                self.app.btn_start.config(text=f"{lang_map['開始錄製']} ({hotkey_map.get('start', '')})")
                self.app.btn_pause.config(text=f"{lang_map['暫停/繼續']} ({hotkey_map.get('pause', '')})")
                self.app.btn_stop.config(text=f"{lang_map['停止']} ({hotkey_map.get('stop', '')})")
                self.app.btn_play.config(text=f"{lang_map['回放']} ({hotkey_map.get('play', '')})")
            except ImportError:
                # Fallback 文字
                self.app.btn_start.config(text=f"開始錄製 ({hotkey_map.get('start', '')})")
                self.app.btn_pause.config(text=f"暫停/繼續 ({hotkey_map.get('pause', '')})")
                self.app.btn_stop.config(text=f"停止 ({hotkey_map.get('stop', '')})")
                self.app.btn_play.config(text=f"回放 ({hotkey_map.get('play', '')})")
        
        # 更新 MiniMode 按鈕（如果有的話）
        if hasattr(self.app, 'mini_controller') and self.app.mini_controller:
            try:
                self.app.mini_controller.update_buttons(hotkey_map)
            except Exception:
                pass
