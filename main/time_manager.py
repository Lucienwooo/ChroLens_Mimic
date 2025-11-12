"""
時間管理器
獨立處理所有時間相關邏輯，使用實際時間確保準確性

作者: Lucien
版本: 1.0.0
日期: 2025/11/12
"""

import time
import threading
from typing import Callable, Optional, Tuple


class TimeManager:
    """
    管理錄製時間、回放時間、倒數計時
    
    設計特點:
    1. 使用實際時間（time.time()）而非事件索引
    2. 支援速度調整
    3. 支援暫停/繼續（累計暫停時間）
    4. 線程安全
    5. 回調機制解耦 UI 更新
    """
    
    def __init__(self, logger=None):
        """
        初始化時間管理器
        
        Args:
            logger: 日誌函數
        """
        self._lock = threading.RLock()
        self._logger = logger or (lambda msg: print(f"[TimeManager] {msg}"))
        
        # 錄製相關
        self._recording_start = None
        self._recording_pause_start = None
        self._recording_total_pause = 0
        
        # 回放相關
        self._playback_start = None
        self._cycle_start = None
        self._playback_pause_start = None
        self._playback_total_pause = 0
        self._script_duration = 0  # 腳本邏輯長度（秒）
        self._total_duration = 0   # 總運作時間（秒）
        self._speed = 1.0
        self._current_repeat = 0   # 當前循環次數
        
        # UI 更新回調
        self._update_callbacks = {
            'recording': None,    # 錄製時間更新回調
            'countdown': None,    # 單次剩餘時間更新回調
            'total': None         # 總運作剩餘時間更新回調
        }
        
        # 自動更新線程
        self._update_thread = None
        self._update_running = False
    
    # ========================================
    # 錄製相關方法
    # ========================================
    
    def start_recording(self):
        """開始錄製計時"""
        with self._lock:
            self._recording_start = time.time()
            self._recording_total_pause = 0
            self._recording_pause_start = None
            self._logger("開始錄製計時")
    
    def pause_recording(self):
        """暫停錄製計時"""
        with self._lock:
            if self._recording_start and not self._recording_pause_start:
                self._recording_pause_start = time.time()
                self._logger("暫停錄製計時")
    
    def resume_recording(self):
        """繼續錄製計時"""
        with self._lock:
            if self._recording_pause_start:
                pause_duration = time.time() - self._recording_pause_start
                self._recording_total_pause += pause_duration
                self._recording_pause_start = None
                self._logger(f"繼續錄製計時（暫停了 {pause_duration:.2f} 秒）")
    
    def stop_recording(self):
        """停止錄製計時"""
        with self._lock:
            elapsed = self.get_recording_time()
            self._recording_start = None
            self._recording_pause_start = None
            self._recording_total_pause = 0
            self._logger(f"停止錄製計時（總計 {elapsed:.2f} 秒）")
            return elapsed
    
    def get_recording_time(self) -> float:
        """
        獲取錄製經過時間（排除暫停時間）
        
        Returns:
            經過的秒數
        """
        with self._lock:
            if not self._recording_start:
                return 0.0
            
            current_time = time.time()
            elapsed = current_time - self._recording_start - self._recording_total_pause
            
            # 如果正在暫停，還要減去當前暫停的時間
            if self._recording_pause_start:
                current_pause = current_time - self._recording_pause_start
                elapsed -= current_pause
            
            return max(0.0, elapsed)
    
    # ========================================
    # 回放相關方法
    # ========================================
    
    def start_playback(self, script_duration: float, total_duration: float, speed: float = 1.0):
        """
        開始回放計時
        
        Args:
            script_duration: 腳本邏輯長度（秒）
            total_duration: 總運作時間（秒），可以是 float('inf')
            speed: 回放速度倍率
        """
        with self._lock:
            self._playback_start = time.time()
            self._cycle_start = time.time()
            self._playback_total_pause = 0
            self._playback_pause_start = None
            self._script_duration = script_duration
            self._total_duration = total_duration
            self._speed = speed
            self._current_repeat = 0
            self._logger(f"開始回放計時（腳本: {script_duration:.2f}s, 總時間: {total_duration:.2f}s, 速度: {speed}x）")
    
    def pause_playback(self):
        """暫停回放計時"""
        with self._lock:
            if self._playback_start and not self._playback_pause_start:
                self._playback_pause_start = time.time()
                self._logger("暫停回放計時")
    
    def resume_playback(self):
        """繼續回放計時"""
        with self._lock:
            if self._playback_pause_start:
                pause_duration = time.time() - self._playback_pause_start
                self._playback_total_pause += pause_duration
                self._playback_pause_start = None
                self._logger(f"繼續回放計時（暫停了 {pause_duration:.2f} 秒）")
    
    def stop_playback(self):
        """停止回放計時"""
        with self._lock:
            elapsed = self.get_total_elapsed_time()
            self._playback_start = None
            self._cycle_start = None
            self._playback_pause_start = None
            self._playback_total_pause = 0
            self._script_duration = 0
            self._total_duration = 0
            self._current_repeat = 0
            self._logger(f"停止回放計時（總計 {elapsed:.2f} 秒）")
    
    def reset_cycle(self, repeat_number: int = None):
        """
        重置當前循環計時（新的重複循環開始）
        
        Args:
            repeat_number: 當前循環次數（可選）
        """
        with self._lock:
            self._cycle_start = time.time()
            if repeat_number is not None:
                self._current_repeat = repeat_number
            else:
                self._current_repeat += 1
            self._logger(f"重置循環計時（第 {self._current_repeat + 1} 次）")
    
    def get_cycle_time(self) -> float:
        """
        獲取當前循環的回放時間（邏輯時間，應用速度係數）
        
        Returns:
            當前循環經過的邏輯秒數
        """
        with self._lock:
            if not self._cycle_start:
                return 0.0
            
            current_time = time.time()
            real_elapsed = current_time - self._cycle_start
            
            # 如果正在暫停，減去暫停時間
            if self._playback_pause_start:
                real_elapsed -= (current_time - self._playback_pause_start)
            
            # 應用速度係數
            logical_elapsed = real_elapsed * self._speed
            
            # 限制不超過腳本長度
            return min(logical_elapsed, self._script_duration)
    
    def get_countdown_time(self) -> float:
        """
        獲取單次剩餘時間（邏輯時間）
        
        Returns:
            剩餘的邏輯秒數
        """
        elapsed = self.get_cycle_time()
        return max(0.0, self._script_duration - elapsed)
    
    def get_total_elapsed_time(self) -> float:
        """
        獲取總運作經過時間（實際時間）
        
        Returns:
            總經過的實際秒數
        """
        with self._lock:
            if not self._playback_start:
                return 0.0
            
            current_time = time.time()
            elapsed = current_time - self._playback_start - self._playback_total_pause
            
            # 如果正在暫停，減去當前暫停時間
            if self._playback_pause_start:
                elapsed -= (current_time - self._playback_pause_start)
            
            return max(0.0, elapsed)
    
    def get_total_remaining(self) -> float:
        """
        獲取總運作剩餘時間
        
        Returns:
            剩餘的實際秒數，可能是 float('inf')
        """
        if self._total_duration == float('inf'):
            return float('inf')
        
        elapsed = self.get_total_elapsed_time()
        return max(0.0, self._total_duration - elapsed)
    
    def get_current_repeat(self) -> int:
        """獲取當前循環次數"""
        with self._lock:
            return self._current_repeat
    
    # ========================================
    # 回調管理
    # ========================================
    
    def register_callback(self, callback_type: str, callback: Callable[[float], None]):
        """
        註冊時間更新回調
        
        Args:
            callback_type: 'recording' | 'countdown' | 'total'
            callback: 回調函數，接收時間（秒）作為參數
        """
        if callback_type in self._update_callbacks:
            self._update_callbacks[callback_type] = callback
            self._logger(f"已註冊 {callback_type} 回調")
    
    def unregister_callback(self, callback_type: str):
        """移除回調"""
        if callback_type in self._update_callbacks:
            self._update_callbacks[callback_type] = None
    
    # ========================================
    # 自動更新機制
    # ========================================
    
    def start_auto_update(self, interval: float = 0.1):
        """
        啟動自動更新線程（每 interval 秒觸發一次回調）
        
        Args:
            interval: 更新間隔（秒）
        """
        with self._lock:
            if self._update_running:
                self._logger("自動更新已在運行中")
                return
            
            self._update_running = True
            self._update_thread = threading.Thread(
                target=self._auto_update_loop,
                args=(interval,),
                daemon=True
            )
            self._update_thread.start()
            self._logger(f"已啟動自動更新（間隔 {interval}s）")
    
    def stop_auto_update(self):
        """停止自動更新線程"""
        with self._lock:
            if not self._update_running:
                return
            
            self._update_running = False
            if self._update_thread:
                self._update_thread.join(timeout=1.0)
                self._update_thread = None
            self._logger("已停止自動更新")
    
    def _auto_update_loop(self, interval: float):
        """自動更新循環"""
        while self._update_running:
            try:
                self.update_ui()
            except Exception as e:
                self._logger(f"自動更新錯誤: {e}")
            
            time.sleep(interval)
    
    def update_ui(self):
        """觸發所有註冊的回調（應該定期調用）"""
        # 錄製時間更新
        if self._update_callbacks['recording'] and self._recording_start:
            try:
                self._update_callbacks['recording'](self.get_recording_time())
            except Exception as e:
                self._logger(f"錄製時間回調錯誤: {e}")
        
        # 回放時間更新
        if self._playback_start:
            if self._update_callbacks['countdown']:
                try:
                    self._update_callbacks['countdown'](self.get_countdown_time())
                except Exception as e:
                    self._logger(f"倒數時間回調錯誤: {e}")
            
            if self._update_callbacks['total']:
                try:
                    self._update_callbacks['total'](self.get_total_remaining())
                except Exception as e:
                    self._logger(f"總時間回調錯誤: {e}")
    
    # ========================================
    # 工具方法
    # ========================================
    
    @staticmethod
    def format_time(seconds: float) -> str:
        """
        格式化時間為 HH:MM:SS
        
        Args:
            seconds: 秒數
        
        Returns:
            格式化的時間字符串
        """
        if seconds == float('inf'):
            return "∞"
        
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    
    @staticmethod
    def parse_time(time_str: str) -> float:
        """
        解析時間字符串為秒數
        
        Args:
            time_str: "HH:MM:SS" 或 "MM:SS" 格式
        
        Returns:
            秒數
        """
        if not time_str or time_str == "∞":
            return 0.0
        
        parts = time_str.strip().split(":")
        try:
            if len(parts) == 3:
                h, m, s = map(int, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = map(int, parts)
                return m * 60 + s
            elif len(parts) == 1:
                return int(parts[0])
        except ValueError:
            return 0.0
        
        return 0.0


# ============================================
# 使用示例
# ============================================
if __name__ == "__main__":
    import time as time_module
    
    def on_recording_update(seconds):
        print(f"錄製時間: {TimeManager.format_time(seconds)}")
    
    def on_countdown_update(seconds):
        print(f"單次剩餘: {TimeManager.format_time(seconds)}")
    
    def on_total_update(seconds):
        print(f"總運作剩餘: {TimeManager.format_time(seconds)}")
    
    # 創建時間管理器
    tm = TimeManager()
    
    # 註冊回調
    tm.register_callback('recording', on_recording_update)
    tm.register_callback('countdown', on_countdown_update)
    tm.register_callback('total', on_total_update)
    
    # 測試錄製
    print("=== 測試錄製 ===")
    tm.start_recording()
    for i in range(3):
        time_module.sleep(1)
        tm.update_ui()
    tm.stop_recording()
    
    print("\n=== 測試回放 ===")
    tm.start_playback(script_duration=10.0, total_duration=30.0, speed=2.0)
    for i in range(5):
        time_module.sleep(1)
        tm.update_ui()
    
    print("\n重置循環...")
    tm.reset_cycle(1)
    for i in range(3):
        time_module.sleep(1)
        tm.update_ui()
    
    tm.stop_playback()
    print("\n測試完成")
