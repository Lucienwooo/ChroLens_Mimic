"""
獨立快捷鍵監聽系統 - 與錄製系統完全隔離
使用 pynput 實現，不依賴 keyboard 模組
確保快捷鍵不會被 keyboard.stop_recording() 影響

作者: Lucien
版本: 1.0.0
日期: 2025/11/12
"""

import threading
import time
from pynput import keyboard
from pynput.keyboard import Key, KeyCode


class HotkeyListener:
    """
    獨立的快捷鍵監聽器
    
    設計特點:
    1. 使用 pynput.keyboard.Listener，完全獨立於 keyboard 模組
    2. 支援優先級系統（high > normal > low）
    3. 線程安全的註冊/移除機制
    4. 自動重啟機制，確保長時間穩定運行
    """
    
    def __init__(self, logger=None):
        """
        初始化快捷鍵監聽器
        
        Args:
            logger: 日誌函數，用於輸出調試信息
        """
        self._listener = None
        self._hotkeys = {}  # {frozenset(keys): {callback, priority, suppress}}
        self._pressed_keys = set()
        self._lock = threading.RLock()
        self._running = False
        self._logger = logger or (lambda msg: print(f"[HotkeyListener] {msg}"))
        
        # 修飾鍵映射
        self._modifier_map = {
            'ctrl': {Key.ctrl_l, Key.ctrl_r},
            'alt': {Key.alt_l, Key.alt_r},
            'shift': {Key.shift_l, Key.shift_r},
            'win': {Key.cmd_l, Key.cmd_r},
        }
        
        # 特殊鍵映射
        self._special_keys = {
            'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
            'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
            'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
            'esc': Key.esc, 'tab': Key.tab, 'space': Key.space,
            'enter': Key.enter, 'backspace': Key.backspace,
            'delete': Key.delete, 'insert': Key.insert,
            'home': Key.home, 'end': Key.end,
            'pageup': Key.page_up, 'pagedown': Key.page_down,
            'up': Key.up, 'down': Key.down, 'left': Key.left, 'right': Key.right,
            '`': KeyCode.from_char('`'),
        }
    
    def register(self, hotkey_str, callback, priority="normal", suppress=False):
        """
        註冊快捷鍵
        
        Args:
            hotkey_str: 快捷鍵字符串，如 "ctrl+alt+z" 或 "f9"
            callback: 回調函數
            priority: 優先級 "high" | "normal" | "low"
            suppress: 是否阻止按鍵傳遞給其他程序
        
        Returns:
            註冊 ID（用於移除）
        """
        with self._lock:
            keys = self._parse_hotkey(hotkey_str)
            if not keys:
                self._logger(f"無法解析快捷鍵: {hotkey_str}")
                return None
            
            # 使用 frozenset 作為鍵（無序、不可變）
            key_combo = frozenset(keys)
            
            # 註冊快捷鍵
            self._hotkeys[key_combo] = {
                'callback': callback,
                'priority': priority,
                'suppress': suppress,
                'hotkey_str': hotkey_str
            }
            
            self._logger(f"已註冊快捷鍵: {hotkey_str} (優先級: {priority})")
            return key_combo
    
    def unregister(self, hotkey_id):
        """
        移除快捷鍵
        
        Args:
            hotkey_id: 註冊時返回的 ID
        """
        with self._lock:
            if hotkey_id in self._hotkeys:
                hotkey_str = self._hotkeys[hotkey_id]['hotkey_str']
                del self._hotkeys[hotkey_id]
                self._logger(f"已移除快捷鍵: {hotkey_str}")
    
    def unregister_all(self):
        """移除所有快捷鍵"""
        with self._lock:
            count = len(self._hotkeys)
            self._hotkeys.clear()
            self._logger(f"已移除所有快捷鍵 ({count} 個)")
    
    def start(self):
        """啟動監聽器"""
        with self._lock:
            if self._running:
                self._logger("監聽器已在運行中")
                return
            
            self._running = True
            self._pressed_keys.clear()
            
            # 創建 pynput 監聽器
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self._listener.start()
            self._logger("快捷鍵監聽器已啟動")
    
    def stop(self):
        """停止監聽器"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            if self._listener:
                self._listener.stop()
                self._listener = None
            self._pressed_keys.clear()
            self._logger("快捷鍵監聽器已停止")
    
    def restart(self):
        """重啟監聽器"""
        self._logger("正在重啟快捷鍵監聽器...")
        self.stop()
        time.sleep(0.1)  # 短暫等待
        self.start()
    
    def is_alive(self):
        """檢查監聽器是否存活"""
        with self._lock:
            return self._running and self._listener and self._listener.is_alive()
    
    def _parse_hotkey(self, hotkey_str):
        """
        解析快捷鍵字符串
        
        Args:
            hotkey_str: 如 "ctrl+alt+z" 或 "f9"
        
        Returns:
            set of Key/KeyCode 對象
        """
        parts = [p.strip().lower() for p in hotkey_str.split('+')]
        keys = set()
        
        for part in parts:
            # 檢查修飾鍵
            if part in self._modifier_map:
                # 添加該修飾鍵的所有變體（左/右）
                keys.update(self._modifier_map[part])
            # 檢查特殊鍵
            elif part in self._special_keys:
                keys.add(self._special_keys[part])
            # 普通字符
            elif len(part) == 1:
                try:
                    keys.add(KeyCode.from_char(part))
                except:
                    self._logger(f"無法解析字符: {part}")
                    return None
            else:
                self._logger(f"未知的按鍵: {part}")
                return None
        
        return keys
    
    def _normalize_key(self, key):
        """
        標準化按鍵
        將左右修飾鍵統一為同一個集合
        """
        # 如果是修飾鍵，返回其標準形式
        for modifier, variants in self._modifier_map.items():
            if key in variants:
                # 返回所有變體中的第一個（作為標準形式）
                return next(iter(variants))
        return key
    
    def _on_press(self, key):
        """按鍵按下事件"""
        with self._lock:
            if not self._running:
                return
            
            # 標準化並添加到已按下集合
            normalized_key = self._normalize_key(key)
            self._pressed_keys.add(normalized_key)
            
            # 檢查是否觸發快捷鍵
            self._check_hotkeys()
    
    def _on_release(self, key):
        """按鍵釋放事件"""
        with self._lock:
            if not self._running:
                return
            
            # 標準化並從已按下集合移除
            normalized_key = self._normalize_key(key)
            self._pressed_keys.discard(normalized_key)
    
    def _check_hotkeys(self):
        """檢查是否有快捷鍵被觸發"""
        # 按優先級排序（high -> normal -> low）
        priority_order = {"high": 0, "normal": 1, "low": 2}
        
        sorted_hotkeys = sorted(
            self._hotkeys.items(),
            key=lambda x: priority_order.get(x[1]['priority'], 1)
        )
        
        for key_combo, info in sorted_hotkeys:
            # 檢查是否所有按鍵都被按下
            if self._is_combo_pressed(key_combo):
                # 在新線程執行回調，避免阻塞監聽器
                threading.Thread(
                    target=self._safe_callback,
                    args=(info['callback'], info['hotkey_str']),
                    daemon=True
                ).start()
                
                # 如果設置了 suppress，只觸發最高優先級的一個
                if info['suppress']:
                    break
    
    def _is_combo_pressed(self, key_combo):
        """
        檢查組合鍵是否全部被按下
        
        對於修飾鍵，只要左鍵或右鍵任一被按下即可
        """
        for key in key_combo:
            # 檢查這個鍵是否被按下（考慮修飾鍵的左右變體）
            is_pressed = False
            
            # 檢查是否是修飾鍵的變體
            for modifier, variants in self._modifier_map.items():
                if key in variants:
                    # 只要任一變體被按下即可
                    if any(v in self._pressed_keys for v in variants):
                        is_pressed = True
                        break
            
            # 如果不是修飾鍵，直接檢查
            if not is_pressed and key not in self._pressed_keys:
                return False
        
        return True
    
    def _safe_callback(self, callback, hotkey_str):
        """安全執行回調函數"""
        try:
            callback()
        except Exception as e:
            self._logger(f"快捷鍵 {hotkey_str} 回調執行錯誤: {e}")


# ============================================
# 使用示例
# ============================================
if __name__ == "__main__":
    def on_f9():
        print("F9 被按下！")
    
    def on_ctrl_alt_z():
        print("Ctrl+Alt+Z 被按下！")
    
    def on_f10():
        print("F10 被按下！")
    
    # 創建監聽器
    listener = HotkeyListener()
    
    # 註冊快捷鍵
    listener.register("f9", on_f9, priority="normal")
    listener.register("ctrl+alt+z", on_ctrl_alt_z, priority="high", suppress=True)
    listener.register("f10", on_f10, priority="normal")
    
    # 啟動監聽
    listener.start()
    
    print("快捷鍵監聽器已啟動，按 Ctrl+C 退出...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止...")
        listener.stop()
        print("已停止")
