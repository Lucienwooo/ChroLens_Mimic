"""
集中式狀態管理器
確保應用程式狀態的一致性和線程安全

作者: Lucien
版本: 1.0.0
日期: 2025/11/12
"""

import threading
from enum import Enum
from typing import Callable, List, Optional


class AppState(Enum):
    """應用程式狀態枚舉"""
    IDLE = "idle"                           # 閒置
    RECORDING = "recording"                 # 錄製中
    RECORDING_PAUSED = "recording_paused"   # 錄製暫停
    PLAYING = "playing"                     # 回放中
    PLAYING_PAUSED = "playing_paused"       # 回放暫停


class StateManager:
    """
    集中管理應用程式狀態
    
    設計特點:
    1. 單一真實來源（Single Source of Truth）
    2. 線程安全的狀態轉換
    3. 觀察者模式支援 UI 更新
    4. 狀態轉換驗證
    """
    
    def __init__(self, logger=None):
        """
        初始化狀態管理器
        
        Args:
            logger: 日誌函數
        """
        self._state = AppState.IDLE
        self._lock = threading.RLock()
        self._observers: List[Callable] = []
        self._logger = logger or (lambda msg: print(f"[StateManager] {msg}"))
        
        # 狀態轉換歷史（用於調試）
        self._state_history = []
        self._max_history = 100
    
    def get_state(self) -> AppState:
        """
        獲取當前狀態
        
        Returns:
            當前狀態
        """
        with self._lock:
            return self._state
    
    def set_state(self, new_state: AppState, reason: str = ""):
        """
        設置新狀態（原子操作）
        
        Args:
            new_state: 新狀態
            reason: 狀態變更原因（用於日誌）
        
        Returns:
            是否成功設置
        """
        with self._lock:
            old_state = self._state
            
            # 驗證狀態轉換是否合法
            if not self._is_valid_transition(old_state, new_state):
                self._logger(f"非法狀態轉換: {old_state.value} -> {new_state.value}")
                return False
            
            # 更新狀態
            self._state = new_state
            
            # 記錄歷史
            import time
            self._state_history.append({
                'timestamp': time.time(),
                'old_state': old_state,
                'new_state': new_state,
                'reason': reason
            })
            if len(self._state_history) > self._max_history:
                self._state_history.pop(0)
            
            # 日誌
            reason_str = f" ({reason})" if reason else ""
            self._logger(f"狀態變更: {old_state.value} -> {new_state.value}{reason_str}")
            
            # 通知所有觀察者
            self._notify_observers(old_state, new_state)
            
            return True
    
    def _is_valid_transition(self, old_state: AppState, new_state: AppState) -> bool:
        """
        驗證狀態轉換是否合法
        
        合法的狀態轉換:
        - IDLE -> RECORDING, PLAYING
        - RECORDING -> IDLE, RECORDING_PAUSED
        - RECORDING_PAUSED -> RECORDING, IDLE
        - PLAYING -> IDLE, PLAYING_PAUSED
        - PLAYING_PAUSED -> PLAYING, IDLE
        """
        # 相同狀態始終合法（允許重新進入）
        if old_state == new_state:
            return True
        
        valid_transitions = {
            AppState.IDLE: {AppState.RECORDING, AppState.PLAYING},
            AppState.RECORDING: {AppState.IDLE, AppState.RECORDING_PAUSED},
            AppState.RECORDING_PAUSED: {AppState.RECORDING, AppState.IDLE},
            AppState.PLAYING: {AppState.IDLE, AppState.PLAYING_PAUSED},
            AppState.PLAYING_PAUSED: {AppState.PLAYING, AppState.IDLE},
        }
        
        return new_state in valid_transitions.get(old_state, set())
    
    def is_recording(self) -> bool:
        """是否正在錄製"""
        with self._lock:
            return self._state in [AppState.RECORDING, AppState.RECORDING_PAUSED]
    
    def is_playing(self) -> bool:
        """是否正在回放"""
        with self._lock:
            return self._state in [AppState.PLAYING, AppState.PLAYING_PAUSED]
    
    def is_paused(self) -> bool:
        """是否暫停"""
        with self._lock:
            return self._state in [AppState.RECORDING_PAUSED, AppState.PLAYING_PAUSED]
    
    def is_busy(self) -> bool:
        """是否忙碌（錄製或回放中）"""
        with self._lock:
            return self._state != AppState.IDLE
    
    def is_idle(self) -> bool:
        """是否閒置"""
        with self._lock:
            return self._state == AppState.IDLE
    
    def can_start_recording(self) -> bool:
        """檢查是否可以開始錄製"""
        with self._lock:
            return self._state == AppState.IDLE
    
    def can_start_playing(self) -> bool:
        """檢查是否可以開始回放"""
        with self._lock:
            return self._state == AppState.IDLE
    
    def can_pause(self) -> bool:
        """檢查是否可以暫停"""
        with self._lock:
            return self._state in [AppState.RECORDING, AppState.PLAYING]
    
    def can_resume(self) -> bool:
        """檢查是否可以繼續"""
        with self._lock:
            return self._state in [AppState.RECORDING_PAUSED, AppState.PLAYING_PAUSED]
    
    def can_stop(self) -> bool:
        """檢查是否可以停止"""
        with self._lock:
            return self._state != AppState.IDLE
    
    def start_recording(self, reason: str = "") -> bool:
        """開始錄製"""
        return self.set_state(AppState.RECORDING, reason)
    
    def start_playing(self, reason: str = "") -> bool:
        """開始回放"""
        return self.set_state(AppState.PLAYING, reason)
    
    def pause(self, reason: str = "") -> bool:
        """暫停"""
        with self._lock:
            if self._state == AppState.RECORDING:
                return self.set_state(AppState.RECORDING_PAUSED, reason)
            elif self._state == AppState.PLAYING:
                return self.set_state(AppState.PLAYING_PAUSED, reason)
            return False
    
    def resume(self, reason: str = "") -> bool:
        """繼續"""
        with self._lock:
            if self._state == AppState.RECORDING_PAUSED:
                return self.set_state(AppState.RECORDING, reason)
            elif self._state == AppState.PLAYING_PAUSED:
                return self.set_state(AppState.PLAYING, reason)
            return False
    
    def stop(self, reason: str = "") -> bool:
        """停止（回到閒置）"""
        return self.set_state(AppState.IDLE, reason)
    
    def add_observer(self, callback: Callable[[AppState, AppState], None]):
        """
        添加狀態觀察者
        
        Args:
            callback: 回調函數，接收 (old_state, new_state) 參數
        """
        with self._lock:
            if callback not in self._observers:
                self._observers.append(callback)
    
    def remove_observer(self, callback: Callable[[AppState, AppState], None]):
        """
        移除狀態觀察者
        
        Args:
            callback: 要移除的回調函數
        """
        with self._lock:
            if callback in self._observers:
                self._observers.remove(callback)
    
    def _notify_observers(self, old_state: AppState, new_state: AppState):
        """通知所有觀察者狀態變化"""
        for observer in self._observers:
            try:
                observer(old_state, new_state)
            except Exception as e:
                self._logger(f"狀態觀察者錯誤: {e}")
    
    def get_state_history(self, count: int = 10) -> List[dict]:
        """
        獲取狀態轉換歷史
        
        Args:
            count: 返回最近幾筆記錄
        
        Returns:
            狀態歷史列表
        """
        with self._lock:
            return self._state_history[-count:].copy()
    
    def reset(self):
        """重置狀態管理器"""
        with self._lock:
            self._state = AppState.IDLE
            self._state_history.clear()
            self._logger("狀態管理器已重置")


# ============================================
# 使用示例
# ============================================
if __name__ == "__main__":
    def on_state_change(old_state, new_state):
        print(f"狀態變化: {old_state.value} -> {new_state.value}")
    
    # 創建狀態管理器
    sm = StateManager()
    
    # 添加觀察者
    sm.add_observer(on_state_change)
    
    # 測試狀態轉換
    print("=== 測試狀態轉換 ===")
    print(f"當前狀態: {sm.get_state().value}")
    print(f"是否閒置: {sm.is_idle()}")
    print(f"可以開始錄製: {sm.can_start_recording()}")
    
    print("\n開始錄製...")
    sm.start_recording("用戶點擊按鈕")
    print(f"當前狀態: {sm.get_state().value}")
    print(f"是否正在錄製: {sm.is_recording()}")
    
    print("\n暫停錄製...")
    sm.pause("用戶點擊暫停")
    print(f"當前狀態: {sm.get_state().value}")
    print(f"是否暫停: {sm.is_paused()}")
    
    print("\n繼續錄製...")
    sm.resume("用戶點擊繼續")
    print(f"當前狀態: {sm.get_state().value}")
    
    print("\n停止錄製...")
    sm.stop("用戶點擊停止")
    print(f"當前狀態: {sm.get_state().value}")
    
    print("\n=== 狀態歷史 ===")
    for record in sm.get_state_history():
        print(f"{record['old_state'].value} -> {record['new_state'].value}: {record['reason']}")
