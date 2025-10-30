import keyboard
import mouse
import time
import threading
import ctypes
from pynput.mouse import Controller, Listener
import pynput  # 加入這行

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
                    event = {
                        'type': 'mouse',
                        'event': 'down' if pressed else 'up',
                        'button': str(button).replace('Button.', ''),
                        'x': x,
                        'y': y,
                        'time': time.time()
                    }
                    self._mouse_events.append(event)

            def on_scroll(x, y, dx, dy):
                if self._recording_mouse and not self.paused:
                    event = {
                        'type': 'mouse',
                        'event': 'wheel',
                        'delta': dy,
                        'x': x,
                        'y': y,
                        'time': time.time()
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
            event = {
                'type': 'mouse',
                'event': 'move',
                'x': last_pos[0],
                'y': last_pos[1],
                'time': now
            }
            self._mouse_events.append(event)

            # 持續記錄滑鼠移動
            while self.recording:
                if not self.paused:
                    now = time.time()
                    pos = mouse_ctrl.position
                    if pos != last_pos:
                        event = {
                            'type': 'mouse',
                            'event': 'move',
                            'x': pos[0],
                            'y': pos[1],
                            'time': now
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

            # 過濾掉快捷鍵事件
            filtered_k_events = [
                e for e in all_k_events
                if not (e.name == 'f10' and e.event_type in ('down', 'up'))
            ]

            # 合併所有事件並排序
            self.events = sorted(
                [{'type': 'keyboard', 'event': e.event_type, 'name': e.name, 'time': e.time} 
                 for e in filtered_k_events] +
                self._mouse_events,
                key=lambda e: e['time']
            )

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
                        self._execute_event(event)
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

    def _execute_event(self, event):
        """執行單一事件"""
        if event['type'] == 'keyboard':
            if event['event'] == 'down':
                keyboard.press(event['name'])
            elif event['event'] == 'up':
                keyboard.release(event['name'])
        elif event['type'] == 'mouse':
            if event['event'] == 'move':
                ctypes.windll.user32.SetCursorPos(int(event['x']), int(event['y']))
            elif event['event'] in ('down', 'up'):
                button = event.get('button', 'left')
                self._mouse_event(event['event'], button=button)
            elif event['event'] == 'wheel':
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