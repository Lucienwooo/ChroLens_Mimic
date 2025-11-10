"""
快捷鍵管理器 - Hotkey Manager
負責註冊、取消註冊和管理所有快捷鍵
"""

import keyboard
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
        """註冊所有快捷鍵"""
        self.register_system_hotkeys()
        self.register_script_hotkeys()
    
    def register_system_hotkeys(self):
        """註冊系統快捷鍵（錄製、停止、回放等）"""
        # 先清除所有已註冊的系統快捷鍵
        self.unregister_system_hotkeys()
        
        hotkey_map = self.config.get_all_hotkeys()
        
        # 定義快捷鍵與回調函式的映射
        hotkey_actions = {
            "start": self.app.start_record,
            "pause": self.app.toggle_pause,
            "stop": self.app.stop_all,
            "play": self.app.play_record,
            "mini": self.app.toggle_mini_mode
            ,"force_quit": getattr(self.app, 'force_quit', None)
        }
        
        # 註冊每個快捷鍵
        for key, callback in hotkey_actions.items():
            hotkey = hotkey_map.get(key, "")
            # 如果沒有對應的回調，跳過（例如 force_quit 在某些情況下可能不存在）
            if not callback:
                continue
            if hotkey:
                try:
                    handler = keyboard.add_hotkey(
                        hotkey,
                        callback,
                        suppress=False,
                        trigger_on_release=False
                    )
                    self._system_handlers[key] = handler
                    if hasattr(self.app, 'log'):
                        self.app.log(f"已註冊快捷鍵: {hotkey} → {key}")
                except Exception as ex:
                    if hasattr(self.app, 'log'):
                        self.app.log(f"快捷鍵 {hotkey} 註冊失敗: {ex}")
    
    def register_script_hotkeys(self):
        """註冊所有腳本快捷鍵"""
        # 先清除所有已註冊的腳本快捷鍵
        self.unregister_script_hotkeys()
        
        # 掃描所有腳本並註冊快捷鍵
        scripts = self.script_manager.get_all_scripts()
        
        for script in scripts:
            path = self.script_manager.get_script_path(script)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                hotkey = data.get("script_hotkey", "")
                if hotkey:
                    # 為每個腳本註冊快捷鍵
                    handler = keyboard.add_hotkey(
                        hotkey,
                        lambda s=script: self._play_script_by_hotkey(s),
                        suppress=False,
                        trigger_on_release=False
                    )
                    self._script_handlers[script] = {
                        "handler": handler,
                        "script": script,
                        "hotkey": hotkey
                    }
                    if hasattr(self.app, 'log'):
                        self.app.log(f"已註冊腳本快捷鍵: {hotkey} → {script}")
            except Exception as ex:
                # 忽略讀取錯誤的腳本
                pass
    
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
        """取消註冊所有快捷鍵"""
        self.unregister_system_hotkeys()
        self.unregister_script_hotkeys()
    
    def unregister_system_hotkeys(self):
        """取消註冊系統快捷鍵"""
        for key, handler in list(self._system_handlers.items()):
            try:
                keyboard.remove_hotkey(handler)
            except Exception:
                pass
        self._system_handlers.clear()
    
    def unregister_script_hotkeys(self):
        """取消註冊腳本快捷鍵"""
        for info in self._script_handlers.values():
            try:
                keyboard.remove_hotkey(info.get("handler"))
            except Exception:
                pass
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
            
            # 儲存快捷鍵到腳本
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
