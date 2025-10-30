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
        """停止錄製"""
        if not self.recording:
            return
        self.recording = False
        self.paused = False
        self._keyboard_recording = False
        self.logger(f"[{time.ctime()}] 停止錄製")

    def toggle_pause(self):
        """切換暫停狀態"""
        self.paused = not self.paused
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

            keyboard.start_recording()
            self._keyboard_recording = True

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

            # 使用 pynput.mouse.Listener
            mouse_listener = pynput.mouse.Listener(
                on_click=on_click,
                on_scroll=on_scroll
            )
            mouse_listener.start()

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
            mouse_listener.stop()

            # 處理鍵盤事件
            if self._keyboard_recording:
                k_events = keyboard.stop_recording()
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

        except Exception as ex:
            self.logger(f"錄製執行緒發生錯誤: {ex}")

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
        """停止回放"""
        self.playing = False
        self.paused = False

    def _play_loop(self, speed, repeat, on_event):
        """回放主循環"""
        try:
            for r in range(max(1, repeat)):
                if not self.playing:
                    break

                self._current_play_index = 0
                base_time = self.events[0]['time']
                play_start = time.time()

                while self._current_play_index < len(self.events):
                    if not self.playing:
                        break

                    while self.paused:
                        if not self.playing:
                            break
                        time.sleep(0.05)
                        play_start += 0.05

                    event = self.events[self._current_play_index]
                    event_offset = (event['time'] - base_time) / speed
                    target_time = play_start + event_offset

                    while time.time() < target_time:
                        if not self.playing:
                            break
                        if self.paused:
                            play_start += 0.05
                            target_time += 0.05
                        time.sleep(0.001)

                    if not self.playing:
                        break

                    try:
                        # 檢查事件是否應該被執行
                        # 如果有目標視窗限定，且事件標記為視窗外，則跳過執行但保持時間軸
                        should_execute = True
                        if self._target_hwnd and event.get('type') == 'mouse':
                            # 如果事件標記為不在目標視窗內，跳過執行
                            if not event.get('in_target', True):
                                should_execute = False
                        
                        if should_execute:
                            # 根據後台模式選擇執行方法
                            self._execute_event_with_mode(event)
                        
                        if on_event:
                            on_event(event)
                    except Exception as ex:
                        self.logger(f"執行事件時發生錯誤: {ex}")

                    self._current_play_index += 1

                if not self.playing:
                    break

            self.logger(f"[{time.ctime()}] 回放完成")

        except Exception as ex:
            self.logger(f"回放執行緒發生錯誤: {ex}")
        finally:
            self.playing = False
            self.paused = False

    def _execute_event_with_mode(self, event):
        """根據後台模式執行事件"""
        mode = self._background_mode
        
        # 智能模式：自動選擇最佳方法
        if mode == "smart":
            # 如果有目標視窗，優先嘗試 PostMessage
            if self._target_hwnd:
                success = self._try_postmessage(event)
                if not success:
                    # PostMessage 失敗，改用快速切換
                    self._execute_fast_switch(event)
            else:
                # 沒有目標視窗，使用前景模式
                self._execute_event(event)
        
        # 快速切換模式
        elif mode == "fast_switch":
            if self._target_hwnd:
                self._execute_fast_switch(event)
            else:
                self._execute_event(event)
        
        # 純後台模式（PostMessage）
        elif mode == "postmessage":
            if self._target_hwnd:
                success = self._try_postmessage(event)
                if not success:
                    self.logger("PostMessage 失敗，跳過此事件")
            else:
                self._execute_event(event)
        
        # 前景模式（預設）
        else:
            self._execute_event(event)

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
        """快速切換到目標視窗執行事件"""
        if not self._target_hwnd:
            self._execute_event(event)
            return
        
        try:
            # 記住當前視窗
            current_hwnd = win32gui.GetForegroundWindow()
            
            # 檢查目標視窗是否還存在
            if not win32gui.IsWindow(self._target_hwnd):
                self.logger("目標視窗已關閉")
                return
            
            # 切換到目標視窗
            try:
                win32gui.SetForegroundWindow(self._target_hwnd)
                time.sleep(0.01)  # 10ms 等待切換完成
            except Exception:
                # 某些視窗可能無法切換，直接執行
                pass
            
            # 執行事件
            self._execute_event(event)
            
            # 切回原視窗
            try:
                if current_hwnd and win32gui.IsWindow(current_hwnd):
                    win32gui.SetForegroundWindow(current_hwnd)
            except Exception:
                pass
        
        except Exception as ex:
            self.logger(f"快速切換執行失敗: {ex}")
            # 失敗時直接執行
            self._execute_event(event)

    def _execute_event(self, event):
        """執行單一事件"""
        if event['type'] == 'keyboard':
            if event['event'] == 'down':
                keyboard.press(event['name'])
            elif event['event'] == 'up':
                keyboard.release(event['name'])
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
            
            if event['event'] == 'move':
                ctypes.windll.user32.SetCursorPos(int(x), int(y))
            elif event['event'] in ('down', 'up'):
                # 先移動到正確位置再執行點擊
                ctypes.windll.user32.SetCursorPos(int(x), int(y))
                time.sleep(0.001)  # 短暫延遲確保座標更新
                button = event.get('button', 'left')
                self._mouse_event(event['event'], button=button)
            elif event['event'] == 'wheel':
                # 先移動到正確位置再執行滾輪
                ctypes.windll.user32.SetCursorPos(int(x), int(y))
                time.sleep(0.001)
                self._mouse_event('wheel', delta=event.get('delta', 0))

    def _mouse_event(self, event, button='left', delta=0):
        """執行滑鼠事件"""
        user32 = ctypes.windll.user32
        if event == 'down' or event == 'up':
            flags = {
                'left': (0x0002, 0x0004),
                'right': (0x0008, 0x0010),
                'middle': (0x0020, 0x0040)
            }
            flag = flags.get(button, (0x0002, 0x0004))[0 if event == 'down' else 1]
            
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
                
            inp = INPUT()
            inp.type = 0
            inp.mi = MOUSEINPUT(0, 0, 0, flag, 0, None)
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
            
        elif event == 'wheel':
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
                
            inp = INPUT()
            inp.type = 0
            inp.mi = MOUSEINPUT(0, 0, int(delta * 120), 0x0800, 0, None)
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))