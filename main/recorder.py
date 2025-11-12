import keyboard
import mouse
import time
import threading
import ctypes
from pynput.mouse import Controller, Listener
import pynput  # 加入這行
import win32gui  # 新增：用於視窗檢測
import win32api
import win32con

class CoreRecorder:
    """錄製和回放的核心類別"""
    
    def __init__(self, logger=None):
        self.logger = logger or (lambda s: None)
        self.recording = False
        self.playing = False
        self.paused = False
        self.events = []
        self._record_thread = None
        self._play_thread = None
        self._record_start_time = None
        self._mouse_events = []
        self._keyboard_recording = False
        self._recording_mouse = False
        self._paused_k_events = []
        self._current_play_index = 0
        self._target_hwnd = None  # 新增：目標視窗 handle
        self._background_mode = "smart"  # 後台模式：smart, fast_switch, postmessage, foreground
        self._mouse_mode = False  # 新增：滑鼠模式（是否控制真實滑鼠）
        self._mouse_listener = None
        self._pressed_keys = set()

    def set_target_window(self, hwnd):
        """設定目標視窗，只錄製/回放該視窗內的操作"""
        self._target_hwnd = hwnd
        if hwnd:
            self.logger(f"已設定目標視窗：hwnd={hwnd}")
        else:
            self.logger("已取消目標視窗限定")

    def set_background_mode(self, mode):
        """設定後台執行模式
        
        Args:
            mode: 執行模式
                - "smart": 智能模式（自動選擇最佳方法）
                - "fast_switch": 快速切換模式（高相容性）
                - "postmessage": 純後台模式（PostMessage）
                - "foreground": 前景模式（預設，移動真實滑鼠）
        """
        valid_modes = ["smart", "fast_switch", "postmessage", "foreground"]
        if mode in valid_modes:
            self._background_mode = mode
            self.logger(f"已設定後台模式：{mode}")
        else:
            self.logger(f"無效的模式：{mode}，保持目前設定")
    
    def set_mouse_mode(self, enabled):
        """設定滑鼠模式
        
        Args:
            enabled: True = 控制真實滑鼠游標, False = 使用後台模式
        """
        self._mouse_mode = enabled
        if enabled:
            self.logger(f"滑鼠模式：已啟用（將控制真實滑鼠游標）")
        else:
            self.logger(f"滑鼠模式：已停用（使用後台模式）")

    def _screen_to_client(self, hwnd, screen_x, screen_y):
        """將螢幕座標轉換為視窗內座標"""
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            client_x = screen_x - left
            client_y = screen_y - top
            return client_x, client_y
        except Exception:
            return screen_x, screen_y

    def _name_to_vk(self, key_name):
        """將按鍵名稱轉換為虛擬鍵碼"""
        # 常用按鍵映射
        key_map = {
            'enter': win32con.VK_RETURN,
            'space': win32con.VK_SPACE,
            'tab': win32con.VK_TAB,
            'backspace': win32con.VK_BACK,
            'delete': win32con.VK_DELETE,
            'esc': win32con.VK_ESCAPE,
            'shift': win32con.VK_SHIFT,
            'ctrl': win32con.VK_CONTROL,
            'alt': win32con.VK_MENU,
            'left': win32con.VK_LEFT,
            'right': win32con.VK_RIGHT,
            'up': win32con.VK_UP,
            'down': win32con.VK_DOWN,
        }
        
        # F1-F12
        for i in range(1, 13):
            key_map[f'f{i}'] = win32con.VK_F1 + i - 1
        
        # 字母和數字
        if len(key_name) == 1:
            if key_name.isalpha():
                return ord(key_name.upper())
            elif key_name.isdigit():
                return ord(key_name)
        
        return key_map.get(key_name.lower(), 0)

    def start_record(self):
        """開始錄製"""
        if self.recording:
            return
        self.recording = True
        self.paused = False
        self.events = []
        self._record_start_time = time.time()
        self.logger(f"[{time.ctime()}] 開始錄製")
        self._record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self._record_thread.start()
        return self._record_start_time

    def stop_record(self):
        """停止錄製（穩定增強版 - 添加清理鎖與重試機制）"""
        if not self.recording:
            return
        
        # ✅ 修復：先標記停止，讓錄製迴圈結束
        self.recording = False
        self.paused = False
        self._recording_mouse = False
        
        self.logger(f"[{time.ctime()}] 停止錄製（等待事件處理完成...）")
        
        # ✅ 穩定性增強：使用鎖保護 keyboard hook 清理，並添加重試機制
        try:
            # 只有在真正有啟動錄製時才嘗試停止
            if self._keyboard_recording:
                # 先重置狀態，避免重複呼叫
                self._keyboard_recording = False
                
                # 嘗試停止錄製（添加重試機制）
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        k_events = keyboard.stop_recording()
                        self.logger(f"[停止錄製] 已停止鍵盤錄製 (獲得 {len(k_events) if k_events else 0} 個事件)")
                        break
                    except Exception as retry_ex:
                        if attempt < max_retries - 1:
                            self.logger(f"[重試 {attempt + 1}/{max_retries}] 停止鍵盤錄製: {retry_ex}")
                            time.sleep(0.1)  # 短暫等待後重試
                        else:
                            raise retry_ex
        except Exception as e:
            self.logger(f"[警告] 停止鍵盤錄製時發生錯誤: {e}")
            # ✅ 強制重置狀態，確保下次可以重新開始
            self._keyboard_recording = False
        
        # 嘗試停止並 join mouse listener（若有）以釋放資源
        try:
            if getattr(self, '_mouse_listener', None):
                try:
                    self._mouse_listener.stop()
                    self.logger(f"[停止錄製] 已停止滑鼠監聽器")
                except Exception:
                    pass
                try:
                    self._mouse_listener.join(timeout=1.0)
                except Exception:
                    pass
                self._mouse_listener = None
        except Exception:
            pass
        
        # 釋放播放或錄製期間可能遺留的按鍵
        try:
            self._release_pressed_keys()
        except Exception:
            pass
        
        # ✅ 修復：等待錄製執行緒真正結束
        if hasattr(self, '_record_thread') and self._record_thread:
            try:
                self._record_thread.join(timeout=2.0)
                if self._record_thread.is_alive():
                    self.logger(f"[警告] 錄製執行緒未能在 2 秒內結束")
            except Exception:
                pass
        
        self.logger(f"[停止錄製] 錄製已完全停止，可以開始下一次錄製")

    def toggle_pause(self):
        """切換暫停狀態（改善版）"""
        self.paused = not self.paused
        
        # 錄製時的暫停處理
        if self.recording and hasattr(self, '_keyboard_recording'):
            if self.paused:
                # 暫停時停止 keyboard 錄製，暫存事件
                if self._keyboard_recording:
                    try:
                        k_events = keyboard.stop_recording()
                        if not hasattr(self, "_paused_k_events"):
                            self._paused_k_events = []
                        self._paused_k_events.extend(k_events)
                        self._keyboard_recording = False
                        self.logger("[暫停] 鍵盤錄製已暫停")
                    except Exception as e:
                        self.logger(f"[警告] 暫停鍵盤錄製時發生錯誤: {e}")
            else:
                # 繼續時重新開始 keyboard 錄製
                try:
                    keyboard.start_recording()
                    self._keyboard_recording = True
                    self.logger("[繼續] 鍵盤錄製已繼續")
                except Exception as e:
                    self.logger(f"[警告] 繼續鍵盤錄製時發生錯誤: {e}")
                    self._keyboard_recording = False
        
        return self.paused

    def _is_point_in_target_window(self, x, y):
        """檢查座標是否在目標視窗內"""
        if not self._target_hwnd:
            return True  # 沒有設定目標視窗，全部接受
        try:
            # 取得滑鼠所在位置的視窗
            point = ctypes.wintypes.POINT(int(x), int(y))
            hwnd_at_point = ctypes.windll.user32.WindowFromPoint(point)
            
            # 檢查是否為目標視窗或其子視窗
            current_hwnd = hwnd_at_point
            while current_hwnd:
                if current_hwnd == self._target_hwnd:
                    return True
                try:
                    current_hwnd = win32gui.GetParent(current_hwnd)
                except:
                    break
            return False
        except:
            return True  # 發生錯誤時不過濾

    def _record_loop(self):
        """錄製主循環"""
        try:
            self._mouse_events = []
            self._recording_mouse = True
            self._record_start_time = time.time()
            self._paused_k_events = []

            # 嘗試啟動 keyboard 錄製（可能在打包後失敗）
            try:
                keyboard.start_recording()
                self._keyboard_recording = True
                self.logger("[錄製] keyboard 模組已啟動")
            except Exception as e:
                self._keyboard_recording = False
                self.logger(f"[警告] keyboard 模組啟動失敗（可能需要管理員權限）: {e}")

            mouse_ctrl = Controller()
            last_pos = mouse_ctrl.position

            def on_click(x, y, button, pressed):
                if self._recording_mouse and not self.paused:
                    # 記錄所有點擊事件，但標記是否在目標視窗內
                    in_target = self._is_point_in_target_window(x, y)
                    event = {
                        'type': 'mouse',
                        'event': 'down' if pressed else 'up',
                        'button': str(button).replace('Button.', ''),
                        'x': x,
                        'y': y,
                        'time': time.time(),
                        'in_target': in_target  # 標記是否在目標視窗內
                    }
                    self._mouse_events.append(event)

            def on_scroll(x, y, dx, dy):
                if self._recording_mouse and not self.paused:
                    # 記錄所有滾輪事件，但標記是否在目標視窗內
                    in_target = self._is_point_in_target_window(x, y)
                    event = {
                        'type': 'mouse',
                        'event': 'wheel',
                        'delta': dy,
                        'x': x,
                        'y': y,
                        'time': time.time(),
                        'in_target': in_target  # 標記是否在目標視窗內
                    }
                    self._mouse_events.append(event)

            # 使用 pynput.mouse.Listener（添加錯誤處理）
            mouse_listener = None
            try:
                mouse_listener = pynput.mouse.Listener(
                    on_click=on_click,
                    on_scroll=on_scroll
                )
                mouse_listener.start()
                # 儲存 reference，以便外部能停止/join
                try:
                    self._mouse_listener = mouse_listener
                except Exception:
                    pass
                self.logger("[錄製] pynput.mouse.Listener 已啟動")
            except Exception as e:
                self.logger(f"[警告] pynput.mouse.Listener 啟動失敗（可能需要管理員權限）: {e}")
                # 如果 listener 失敗，仍然可以記錄移動

            # 記錄初始位置
            now = time.time()
            in_target = self._is_point_in_target_window(last_pos[0], last_pos[1])
            event = {
                'type': 'mouse',
                'event': 'move',
                'x': last_pos[0],
                'y': last_pos[1],
                'time': now,
                'in_target': in_target
            }
            self._mouse_events.append(event)

            # 持續記錄滑鼠移動
            while self.recording:
                if not self.paused:
                    now = time.time()
                    pos = mouse_ctrl.position
                    if pos != last_pos:
                        # 記錄所有移動，但標記是否在目標視窗內
                        in_target = self._is_point_in_target_window(pos[0], pos[1])
                        event = {
                            'type': 'mouse',
                            'event': 'move',
                            'x': pos[0],
                            'y': pos[1],
                            'time': now,
                            'in_target': in_target  # 標記是否在目標視窗內
                        }
                        self._mouse_events.append(event)
                        last_pos = pos
                time.sleep(0.01)  # 10ms sampling

            # 停止錄製
            self._recording_mouse = False
            if mouse_listener:
                try:
                    mouse_listener.stop()
                    self.logger("[錄製] pynput.mouse.Listener 已停止")
                except Exception as e:
                    self.logger(f"[警告] 停止 mouse listener 時發生錯誤: {e}")

            # 處理鍵盤事件（添加錯誤處理）
            if self._keyboard_recording:
                try:
                    k_events = keyboard.stop_recording()
                    self.logger("[錄製] keyboard 錄製已停止")
                except Exception as e:
                    self.logger(f"[警告] 停止 keyboard 錄製時發生錯誤: {e}")
                    k_events = []
            else:
                k_events = []

            # 合併暫停期間的事件
            all_k_events = []
            if hasattr(self, "_paused_k_events"):
                all_k_events.extend(self._paused_k_events)
            all_k_events.extend(k_events)

            # 過濾掉快捷鍵事件 (F9, F10, F11, F12)
            filtered_k_events = [
                e for e in all_k_events
                if not (e.name in ('f9', 'f10', 'f11', 'f12') and e.event_type in ('down', 'up'))
            ]

            # 合併所有事件並排序
            self.events = sorted(
                [{'type': 'keyboard', 'event': e.event_type, 'name': e.name, 'time': e.time} 
                 for e in filtered_k_events] +
                self._mouse_events,
                key=lambda e: e['time']
            )

            # 統計視窗內外的事件數量（如果有設定目標視窗）
            if self._target_hwnd:
                mouse_in_target = sum(1 for e in self._mouse_events if e.get('in_target', True))
                mouse_out_target = len(self._mouse_events) - mouse_in_target
                self.logger(f"錄製完成，共 {len(self.events)} 筆事件。")
                self.logger(f"  滑鼠事件：{len(self._mouse_events)} 筆（視窗內: {mouse_in_target}, 視窗外: {mouse_out_target}）")
                self.logger(f"  鍵盤事件：{len(filtered_k_events)} 筆")
            else:
                self.logger(f"錄製完成，共 {len(self.events)} 筆事件。")
            
            # 如果完全沒有事件，顯示警告
            if len(self.events) == 0:
                self.logger("⚠️ 警告：沒有錄製到任何事件！")
                self.logger("可能原因：")
                self.logger("  1. 程式需要以管理員身份執行")
                self.logger("  2. 防毒軟體阻擋了鍵盤/滑鼠監聽")
                self.logger("  3. 系統安全設定阻止了 hook 功能")
                self.logger("建議：請以管理員身份執行此程式")

        except Exception as ex:
            self.logger(f"錄製執行緒發生錯誤: {ex}")
            import traceback
            self.logger(f"詳細錯誤: {traceback.format_exc()}")

    def play(self, speed=1.0, repeat=1, on_event=None):
        """開始回放錄製的事件"""
        if self.playing or not self.events:
            return False
        self.playing = True
        self.paused = False
        self._play_thread = threading.Thread(
            target=self._play_loop,
            args=(speed, repeat, on_event),
            daemon=True
        )
        self._play_thread.start()
        return True

    def stop_play(self):
        """停止回放（強化版 - 確保狀態正確重置）"""
        was_playing = self.playing
        self.playing = False
        self.paused = False
        
        if was_playing:
            self.logger(f"[{time.ctime()}] 已停止回放")
            
            # 釋放可能卡住的修飾鍵
            try:
                import keyboard
                modifiers = ['ctrl', 'shift', 'alt', 'win']
                for mod in modifiers:
                    try:
                        keyboard.release(mod)
                    except:
                        pass
            except:
                pass
        
        # 釋放所有被按下但未 release 的鍵
        try:
            self._release_pressed_keys()
        except Exception:
            pass

    def _play_loop(self, speed, repeat, on_event):
        """回放主循環（強化版 - 支援無限重複，修復點擊其他視窗導致停止的問題）"""
        try:
            # 初始化循環計數器
            self._current_repeat_count = 0
            
            # repeat = -1 表示無限重複
            if repeat == -1:
                r = 0
                while self.playing:
                    if not self.playing:
                        break
                    self._current_repeat_count = r  # ✅ 更新循環計數
                    self._execute_single_round(speed, on_event)
                    r += 1
            else:
                for r in range(max(1, repeat)):
                    if not self.playing:
                        break
                    self._current_repeat_count = r  # ✅ 更新循環計數
                    self._execute_single_round(speed, on_event)
                    
        except Exception as ex:
            self.logger(f"回放循環錯誤: {ex}")
        finally:
            self.playing = False
            self._current_repeat_count = 0  # ✅ 重置循環計數
            
    def _execute_single_round(self, speed, on_event):
        """執行單次回放循環"""
        self._current_play_index = 0
        base_time = self.events[0]['time']
        play_start = time.time()
        pause_start_time = None  # 暫停開始時間
        total_pause_time = 0  # 累計暫停時間
        last_pause_state = False  # 上一次的暫停狀態

        while self._current_play_index < len(self.events):
            # 檢查 playing 狀態（不受外部事件影響）
            if not self.playing:
                break

            # 暫停處理：記錄暫停開始時間
            if self.paused:
                if not last_pause_state:
                    # 剛進入暫停狀態
                    pause_start_time = time.time()
                    last_pause_state = True
                    self.logger("[暫停] 回放已暫停")
                time.sleep(0.05)
                continue
            else:
                # 從暫停恢復：累計暫停時長
                if last_pause_state:
                    # 剛從暫停恢復
                    if pause_start_time is not None:
                        pause_duration = time.time() - pause_start_time
                        total_pause_time += pause_duration
                        self.logger(f"[繼續] 回放繼續（暫停了 {pause_duration:.2f} 秒）")
                        pause_start_time = None
                    last_pause_state = False

            event = self.events[self._current_play_index]
            event_offset = (event['time'] - base_time) / speed
            # 考慮暫停時間的目標時間
            target_time = play_start + event_offset + total_pause_time

            # 等待到目標時間（強化版 - 確保時間計算不受干擾）
            while time.time() < target_time:
                if not self.playing:
                    break
                if self.paused:
                    # 進入暫停狀態
                    if not last_pause_state:
                        pause_start_time = time.time()
                        last_pause_state = True
                        self.logger("[暫停] 回放已暫停")
                    break
                # 使用極短的睡眠時間以保持時間計算精確
                sleep_time = min(0.001, target_time - time.time())
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    break  # 避免 busy-wait

            # 如果進入暫停，跳過事件執行
            if self.paused:
                continue

            if not self.playing:
                break

            # 執行事件（使用 try-except 確保單一事件錯誤不影響整體回放）
            try:
                # 檢查事件是否應該被執行
                should_execute = True
                if self._target_hwnd and event.get('type') == 'mouse':
                    # 如果事件標記為不在目標視窗內，跳過執行
                    if not event.get('in_target', True):
                        should_execute = False
                
                if should_execute:
                    # 根據後台模式選擇執行方法
                    self._execute_event_with_mode(event)
                
                # 通知事件已執行（即使有錯誤也要通知，保持進度）
                if on_event:
                    try:
                        on_event(event)
                    except:
                        pass  # 忽略回調錯誤
            except Exception as ex:
                self.logger(f"執行事件時發生錯誤: {ex}")
                # 繼續執行下一個事件，不中斷回放

            # 更新索引（確保一定會執行）
            self._current_play_index += 1

    def _execute_event_with_mode(self, event):
        """根據後台模式和滑鼠模式執行事件（強化版）"""
        # 如果啟用滑鼠模式，直接使用前景模式（控制真實滑鼠）
        if self._mouse_mode:
            self._execute_event(event)
            return
        
        # 否則根據後台模式選擇執行方法
        mode = self._background_mode
        
        # 智能模式：自動選擇最佳方法（多層容錯 - 強化版）
        if mode == "smart":
            if self._target_hwnd:
                # 檢查視窗是否仍然存在
                try:
                    if not win32gui.IsWindow(self._target_hwnd):
                        self.logger("目標視窗已關閉，切換到前景模式")
                        self._execute_event(event)
                        return
                except:
                    pass
                
                # 嘗試多種方式，確保執行成功
                # 1. 優先嘗試 SendMessage（比 PostMessage 更可靠）
                success = self._try_sendmessage_enhanced(event)
                if success:
                    return
                
                # 2. 嘗試 SetForegroundWindow + 直接執行（高相容性）
                try:
                    # 快速切換到前景執行（速度更快，相容性好）
                    current_hwnd = win32gui.GetForegroundWindow()
                    try:
                        win32gui.SetForegroundWindow(self._target_hwnd)
                        time.sleep(0.001)  # 極短延遲確保切換完成
                        self._execute_event(event)
                        # 立即切回
                        if current_hwnd and win32gui.IsWindow(current_hwnd):
                            win32gui.SetForegroundWindow(current_hwnd)
                    except:
                        self._execute_event(event)
                    return
                except Exception as e:
                    self.logger(f"智能模式執行失敗: {e}")
                
                # 3. 最後回退到前景模式
                self._execute_event(event)
            else:
                # 沒有目標視窗，使用前景模式
                self._execute_event(event)
        
        # 快速切換模式（增強穩定性）
        elif mode == "fast_switch":
            if self._target_hwnd:
                try:
                    self._execute_fast_switch_enhanced(event)
                except Exception as e:
                    self.logger(f"快速切換失敗，回退到前景模式: {e}")
                    self._execute_event(event)
            else:
                self._execute_event(event)
        
        # 純後台模式（SendMessage 優先，增強版）
        elif mode == "postmessage":
            if self._target_hwnd:
                # 優先嘗試 SendMessage（同步，更可靠）
                success = self._try_sendmessage_enhanced(event)
                if not success:
                    # 回退到 PostMessage（異步）
                    success = self._try_postmessage(event)
                    if not success:
                        self.logger("後台模式執行失敗，嘗試前景模式")
                        self._execute_event(event)
            else:
                self._execute_event(event)
        
        # 前景模式（預設）
        else:
            self._execute_event(event)

    def _try_sendmessage_enhanced(self, event):
        """增強版 SendMessage（更可靠的同步執行）"""
        if not self._target_hwnd:
            return False
        
        try:
            # 確保視窗存在且可見
            if not win32gui.IsWindow(self._target_hwnd):
                return False
            
            # 如果視窗最小化，嘗試恢復（但不切換焦點）
            if win32gui.IsIconic(self._target_hwnd):
                try:
                    win32gui.ShowWindow(self._target_hwnd, win32con.SW_RESTORE)
                    time.sleep(0.01)
                except:
                    pass
            
            if event['type'] == 'mouse':
                # 轉換為視窗內座標
                x, y = self._screen_to_client(self._target_hwnd, event['x'], event['y'])
                lParam = win32api.MAKELONG(x, y)
                
                if event['event'] == 'move':
                    # 移動事件使用 SendMessage（同步）
                    win32api.SendMessage(self._target_hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
                    # 額外發送 WM_SETCURSOR 確保游標更新
                    try:
                        win32api.SendMessage(self._target_hwnd, win32con.WM_SETCURSOR, self._target_hwnd, 
                                           win32api.MAKELONG(win32con.HTCLIENT, win32con.WM_MOUSEMOVE))
                    except:
                        pass
                    
                elif event['event'] == 'down':
                    button = event.get('button', 'left')
                    if button == 'left':
                        # 先發送 MOUSEMOVE 確保位置正確
                        win32api.SendMessage(self._target_hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
                        time.sleep(0.001)
                        win32api.SendMessage(self._target_hwnd, win32con.WM_LBUTTONDOWN, 
                                           win32con.MK_LBUTTON, lParam)
                    elif button == 'right':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
                        time.sleep(0.001)
                        win32api.SendMessage(self._target_hwnd, win32con.WM_RBUTTONDOWN, 
                                           win32con.MK_RBUTTON, lParam)
                    elif button == 'middle':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
                        time.sleep(0.001)
                        win32api.SendMessage(self._target_hwnd, win32con.WM_MBUTTONDOWN, 
                                           win32con.MK_MBUTTON, lParam)
                        
                elif event['event'] == 'up':
                    button = event.get('button', 'left')
                    if button == 'left':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_LBUTTONUP, 0, lParam)
                    elif button == 'right':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_RBUTTONUP, 0, lParam)
                    elif button == 'middle':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_MBUTTONUP, 0, lParam)
                        
                elif event['event'] == 'wheel':
                    delta = event.get('delta', 0)
                    wParam = win32api.MAKELONG(0, int(delta * 120))
                    win32api.SendMessage(self._target_hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)
                    
                return True
            
            elif event['type'] == 'keyboard':
                vk_code = self._name_to_vk(event['name'])
                if vk_code:
                    if event['event'] == 'down':
                        # 使用 WM_KEYDOWN 發送按鍵
                        win32api.SendMessage(self._target_hwnd, win32con.WM_KEYDOWN, vk_code, 0)
                        # 對於字元鍵，額外發送 WM_CHAR
                        if 32 <= vk_code <= 126:  # 可顯示字元
                            try:
                                win32api.SendMessage(self._target_hwnd, win32con.WM_CHAR, vk_code, 0)
                            except:
                                pass
                    elif event['event'] == 'up':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_KEYUP, vk_code, 0)
                    return True
            
            return False
            
        except Exception as ex:
            self.logger(f"SendMessage Enhanced 失敗: {ex}")
            return False

    def _execute_fast_switch_enhanced(self, event):
        """增強版快速切換（更穩定的前景切換）"""
        if not self._target_hwnd:
            self._execute_event(event)
            return
        
        try:
            # 檢查目標視窗是否還存在且可見
            if not win32gui.IsWindow(self._target_hwnd):
                self.logger("目標視窗已關閉")
                return
            
            # 如果視窗最小化，先恢復
            if win32gui.IsIconic(self._target_hwnd):
                try:
                    win32gui.ShowWindow(self._target_hwnd, win32con.SW_RESTORE)
                    time.sleep(0.02)
                except:
                    pass
            
            # 記住當前視窗
            current_hwnd = win32gui.GetForegroundWindow()
            
            # 切換到目標視窗（多種方法確保成功）
            switched = False
            try:
                # 方法1: 標準切換
                win32gui.SetForegroundWindow(self._target_hwnd)
                time.sleep(0.002)  # 2ms 極短延遲
                
                # 驗證是否成功切換
                if win32gui.GetForegroundWindow() == self._target_hwnd:
                    switched = True
                else:
                    # 方法2: 使用 BringWindowToTop
                    try:
                        win32gui.BringWindowToTop(self._target_hwnd)
                        win32gui.SetForegroundWindow(self._target_hwnd)
                        time.sleep(0.002)
                        switched = (win32gui.GetForegroundWindow() == self._target_hwnd)
                    except:
                        pass
                    
                    if not switched:
                        # 方法3: 使用 SwitchToThisWindow
                        try:
                            ctypes.windll.user32.SwitchToThisWindow(self._target_hwnd, True)
                            time.sleep(0.003)
                            switched = (win32gui.GetForegroundWindow() == self._target_hwnd)
                        except:
                            pass
                            
            except Exception as e:
                self.logger(f"切換視窗失敗: {e}")
            
            # 執行事件
            self._execute_event(event)
            
            # 極短延遲確保事件執行完成
            if event.get('type') == 'mouse':
                if event.get('event') in ('down', 'up', 'wheel'):
                    time.sleep(0.002)  # 2ms
            
            # 切回原視窗（如果需要且可能）
            if current_hwnd and win32gui.IsWindow(current_hwnd):
                try:
                    win32gui.SetForegroundWindow(current_hwnd)
                except Exception:
                    pass  # 切換失敗不影響執行
        
        except Exception as ex:
            self.logger(f"快速切換執行失敗: {ex}")
            # 失敗時直接執行
            self._execute_event(event)

    def _try_sendmessage(self, event):
        """嘗試使用 SendMessage 執行事件（同步，更可靠）"""
        if not self._target_hwnd:
            return False
        
        try:
            if event['type'] == 'mouse':
                # 轉換為視窗內座標
                x, y = self._screen_to_client(self._target_hwnd, event['x'], event['y'])
                lParam = win32api.MAKELONG(x, y)
                
                if event['event'] == 'move':
                    win32api.SendMessage(self._target_hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
                elif event['event'] == 'down':
                    button = event.get('button', 'left')
                    if button == 'left':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_LBUTTONDOWN, 
                                           win32con.MK_LBUTTON, lParam)
                    elif button == 'right':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_RBUTTONDOWN, 
                                           win32con.MK_RBUTTON, lParam)
                    elif button == 'middle':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_MBUTTONDOWN, 
                                           win32con.MK_MBUTTON, lParam)
                elif event['event'] == 'up':
                    button = event.get('button', 'left')
                    if button == 'left':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_LBUTTONUP, 0, lParam)
                    elif button == 'right':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_RBUTTONUP, 0, lParam)
                    elif button == 'middle':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_MBUTTONUP, 0, lParam)
                elif event['event'] == 'wheel':
                    delta = event.get('delta', 0)
                    wParam = win32api.MAKELONG(0, int(delta * 120))
                    win32api.SendMessage(self._target_hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)
                return True
            
            elif event['type'] == 'keyboard':
                vk_code = self._name_to_vk(event['name'])
                if vk_code:
                    if event['event'] == 'down':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_KEYDOWN, vk_code, 0)
                    elif event['event'] == 'up':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_KEYUP, vk_code, 0)
                    return True
            
            return False
        except Exception as ex:
            self.logger(f"SendMessage 失敗: {ex}")
            return False

    def _try_postmessage(self, event):
        """嘗試使用 PostMessage 執行事件（純後台）"""
        if not self._target_hwnd:
            return False
        
        try:
            if event['type'] == 'mouse':
                # 轉換為視窗內座標
                x, y = self._screen_to_client(self._target_hwnd, event['x'], event['y'])
                lParam = win32api.MAKELONG(x, y)
                
                if event['event'] == 'move':
                    win32api.PostMessage(self._target_hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
                elif event['event'] == 'down':
                    button = event.get('button', 'left')
                    if button == 'left':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_LBUTTONDOWN, 
                                           win32con.MK_LBUTTON, lParam)
                    elif button == 'right':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_RBUTTONDOWN, 
                                           win32con.MK_RBUTTON, lParam)
                    elif button == 'middle':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_MBUTTONDOWN, 
                                           win32con.MK_MBUTTON, lParam)
                elif event['event'] == 'up':
                    button = event.get('button', 'left')
                    if button == 'left':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_LBUTTONUP, 0, lParam)
                    elif button == 'right':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_RBUTTONUP, 0, lParam)
                    elif button == 'middle':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_MBUTTONUP, 0, lParam)
                elif event['event'] == 'wheel':
                    delta = event.get('delta', 0)
                    wParam = win32api.MAKELONG(0, int(delta * 120))
                    win32api.PostMessage(self._target_hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)
                return True
            
            elif event['type'] == 'keyboard':
                vk_code = self._name_to_vk(event['name'])
                if vk_code:
                    if event['event'] == 'down':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_KEYDOWN, vk_code, 0)
                    elif event['event'] == 'up':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_KEYUP, vk_code, 0)
                    return True
            
            return False
        except Exception as ex:
            self.logger(f"PostMessage 失敗: {ex}")
            return False

    def _execute_fast_switch(self, event):
        """快速切換到目標視窗執行事件（增強版）"""
        if not self._target_hwnd:
            self._execute_event(event)
            return
        
        try:
            # 檢查目標視窗是否還存在且可見
            if not win32gui.IsWindow(self._target_hwnd):
                self.logger("目標視窗已關閉")
                return
            
            if not win32gui.IsWindowVisible(self._target_hwnd):
                self.logger("目標視窗不可見，嘗試顯示")
                win32gui.ShowWindow(self._target_hwnd, win32con.SW_SHOW)
                time.sleep(0.05)
            
            # 記住當前視窗
            current_hwnd = win32gui.GetForegroundWindow()
            
            # 切換到目標視窗（增強切換邏輯）
            try:
                # 方法1: 標準切換
                win32gui.SetForegroundWindow(self._target_hwnd)
                time.sleep(0.01)  # 10ms 等待切換完成
                
                # 驗證是否成功切換
                if win32gui.GetForegroundWindow() != self._target_hwnd:
                    # 方法2: 強制切換（使用 SwitchToThisWindow）
                    try:
                        ctypes.windll.user32.SwitchToThisWindow(self._target_hwnd, True)
                        time.sleep(0.02)
                    except:
                        pass
                    
                    # 方法3: 使用 BringWindowToTop
                    try:
                        win32gui.BringWindowToTop(self._target_hwnd)
                        win32gui.SetForegroundWindow(self._target_hwnd)
                        time.sleep(0.02)
                    except:
                        pass
            except Exception as e:
                self.logger(f"切換視窗失敗: {e}")
            
            # 執行事件
            self._execute_event(event)
            
            # 延遲確保事件執行完成
            if event.get('type') == 'mouse':
                if event.get('event') in ('down', 'up', 'wheel'):
                    time.sleep(0.005)  # 5ms
            
            # 切回原視窗（增強切換回邏輯）
            if current_hwnd and win32gui.IsWindow(current_hwnd):
                try:
                    win32gui.SetForegroundWindow(current_hwnd)
                except Exception:
                    # 如果切換失敗，嘗試其他方法
                    try:
                        ctypes.windll.user32.SwitchToThisWindow(current_hwnd, True)
                    except:
                        pass
        
        except Exception as ex:
            self.logger(f"快速切換執行失敗: {ex}")
            # 失敗時直接執行
            self._execute_event(event)

    def _execute_event(self, event):
        """執行單一事件（滑鼠模式 - 強化版）"""
        if event['type'] == 'keyboard':
            # 鍵盤事件執行
            try:
                if event['event'] == 'down':
                    keyboard.press(event['name'])
                    try:
                        self._pressed_keys.add(event['name'])
                    except Exception:
                        pass
                elif event['event'] == 'up':
                    keyboard.release(event['name'])
                    try:
                        if event['name'] in self._pressed_keys:
                            self._pressed_keys.discard(event['name'])
                    except Exception:
                        pass
            except Exception as e:
                self.logger(f"鍵盤事件執行失敗: {e}")
                
        elif event['type'] == 'mouse':
            x, y = event.get('x', 0), event.get('y', 0)
            
            # 如果有設定目標視窗，先確保視窗在前景並將座標限制在視窗內
            if self._target_hwnd:
                try:
                    # 取得視窗矩形
                    left, top, right, bottom = win32gui.GetWindowRect(self._target_hwnd)
                    # 將座標限制在視窗範圍內
                    x = max(left, min(right - 1, x))
                    y = max(top, min(bottom - 1, y))
                except:
                    pass  # 視窗可能已關閉，使用原始座標
            
            try:
                if event['event'] == 'move':
                    # 滑鼠移動（使用硬體級別的 SetCursorPos 確保精確）
                    ctypes.windll.user32.SetCursorPos(int(x), int(y))
                    
                elif event['event'] in ('down', 'up'):
                    # 點擊事件：先移動到正確位置
                    ctypes.windll.user32.SetCursorPos(int(x), int(y))
                    time.sleep(0.001)  # 1ms 短暫延遲確保座標更新
                    
                    button = event.get('button', 'left')
                    self._mouse_event_enhanced(event['event'], button=button)
                    
                elif event['event'] == 'wheel':
                    # 滾輪事件：先移動到正確位置
                    ctypes.windll.user32.SetCursorPos(int(x), int(y))
                    time.sleep(0.001)
                    
                    delta = event.get('delta', 0)
                    self._mouse_event_enhanced('wheel', delta=delta)
                    
            except Exception as e:
                self.logger(f"滑鼠事件執行失敗: {e}")

    def _mouse_event_enhanced(self, event, button='left', delta=0):
        """增強版滑鼠事件執行（更精確穩定）"""
        user32 = ctypes.windll.user32
        
        # 定義 MOUSEINPUT 和 INPUT 結構
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
            ]
            
        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", ctypes.c_ulong),
                ("mi", MOUSEINPUT)
            ]
        
        try:
            if event == 'down' or event == 'up':
                # 按鈕事件標誌
                flags = {
                    'left': (0x0002, 0x0004),    # MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
                    'right': (0x0008, 0x0010),   # MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
                    'middle': (0x0020, 0x0040)   # MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP
                }
                flag = flags.get(button, (0x0002, 0x0004))[0 if event == 'down' else 1]
                
                inp = INPUT()
                inp.type = 0  # INPUT_MOUSE
                inp.mi = MOUSEINPUT(0, 0, 0, flag, 0, None)
                
                # 使用 SendInput 發送輸入（硬體級別）
                result = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
                
                if result == 0:
                    self.logger(f"SendInput 失敗: {ctypes.get_last_error()}")
                
            elif event == 'wheel':
                # 滾輪事件
                inp = INPUT()
                inp.type = 0  # INPUT_MOUSE
                inp.mi = MOUSEINPUT(0, 0, int(delta * 120), 0x0800, 0, None)  # MOUSEEVENTF_WHEEL
                
                result = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
                
                if result == 0:
                    self.logger(f"SendInput (wheel) 失敗: {ctypes.get_last_error()}")
                    
        except Exception as e:
            self.logger(f"滑鼠事件發送失敗: {e}")

    def _release_pressed_keys(self):
        """釋放在回放期間可能被 press 但未 release 的按鍵集合"""
        try:
            import keyboard
            for k in list(getattr(self, '_pressed_keys', [])):
                try:
                    keyboard.release(k)
                except Exception:
                    pass
            self._pressed_keys.clear()
            self.logger("[recorder] 已釋放遺留的按鍵")
        except Exception as ex:
            self.logger(f"[recorder] 釋放遺留按鍵失敗: {ex}")

    def join_threads(self, timeout=1.0):
        """嘗試 join 內部的 record/play thread，回傳是否成功 join"""
        ok = True
        try:
            t = getattr(self, '_record_thread', None)
            if t and getattr(t, 'is_alive', lambda: False)():
                try:
                    t.join(timeout)
                except Exception:
                    ok = False
            p = getattr(self, '_play_thread', None)
            if p and getattr(p, 'is_alive', lambda: False)():
                try:
                    p.join(timeout)
                except Exception:
                    ok = False
        except Exception:
            ok = False
        return ok
