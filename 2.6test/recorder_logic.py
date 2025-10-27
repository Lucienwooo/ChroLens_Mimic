import threading, time, json
import keyboard
from pynput.mouse import Controller, Listener
from config import MOUSE_SAMPLE_INTERVAL
try:
    from utils import screen_to_client, format_time
except Exception:
    def screen_to_client(hwnd, x, y): return x, y
    def format_time(ts):
        import datetime
        return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")

class RecorderLogic:
    def __init__(self, app):
        self.app = app
        self._record_thread_handle = None
        self._recording_mouse = False
        self._paused_k_events = []
        self._keyboard_recording = False
        self._mouse_events = []

    def start_record(self):
        if getattr(self.app, "recording", False):
            return
        self.app.events = []
        self.app.recording = True
        self.app.paused = False
        self.app._record_start_time = time.time()
        self.app.log(f"[{format_time(time.time())}] 開始錄製...")
        self._record_thread_handle = threading.Thread(target=self._record_thread, daemon=True)
        self._record_thread_handle.start()
        self.app.after(100, self._update_record_time)

    def _update_record_time(self):
        if getattr(self.app, "recording", False):
            now = time.time()
            elapsed = now - getattr(self.app, "_record_start_time", now)
            self.app.update_time_label(elapsed)
            self.app.after(100, self._update_record_time)
        else:
            self.app.update_time_label(0)

    def _record_thread(self):
        try:
            self._mouse_events = []
            self._recording_mouse = True
            self._paused_k_events = []
            keyboard.start_recording()
            self._keyboard_recording = True

            mouse_ctrl = Controller()
            last_pos = mouse_ctrl.position

            def on_click(x, y, button, pressed):
                if self._recording_mouse and not self.app.paused:
                    event = {
                        'type': 'mouse',
                        'event': 'down' if pressed else 'up',
                        'button': str(button).replace('Button.', ''),
                        'x': x, 'y': y, 'time': time.time()
                    }
                    if self.app.target_hwnd:
                        rel_x, rel_y = screen_to_client(self.app.target_hwnd, x, y)
                        event.update({'rel_x': rel_x, 'rel_y': rel_y, 'hwnd': self.app.target_hwnd})
                    self._mouse_events.append(event)

            def on_scroll(x, y, dx, dy):
                if self._recording_mouse and not self.app.paused:
                    event = {'type': 'mouse', 'event': 'wheel', 'delta': dy, 'x': x, 'y': y, 'time': time.time()}
                    if self.app.target_hwnd:
                        rel_x, rel_y = screen_to_client(self.app.target_hwnd, x, y)
                        event.update({'rel_x': rel_x, 'rel_y': rel_y, 'hwnd': self.app.target_hwnd})
                    self._mouse_events.append(event)

            mouse_listener = Listener(on_click=on_click, on_scroll=on_scroll)
            mouse_listener.start()

            now = time.time()
            event = {'type': 'mouse', 'event': 'move', 'x': last_pos[0], 'y': last_pos[1], 'time': now}
            if self.app.target_hwnd:
                rel_x, rel_y = screen_to_client(self.app.target_hwnd, last_pos[0], last_pos[1])
                event.update({'rel_x': rel_x, 'rel_y': rel_y, 'hwnd': self.app.target_hwnd})
            self._mouse_events.append(event)

            while getattr(self.app, "recording", False):
                now = time.time()
                pos = mouse_ctrl.position
                if pos != last_pos and not self.app.paused:
                    event = {'type': 'mouse', 'event': 'move', 'x': pos[0], 'y': pos[1], 'time': now}
                    if self.app.target_hwnd:
                        rel_x, rel_y = screen_to_client(self.app.target_hwnd, pos[0], pos[1])
                        event.update({'rel_x': rel_x, 'rel_y': rel_y, 'hwnd': self.app.target_hwnd})
                    self._mouse_events.append(event)
                    last_pos = pos
                time.sleep(MOUSE_SAMPLE_INTERVAL)

            self._recording_mouse = False
            mouse_listener.stop()

            if self._keyboard_recording:
                k_events = keyboard.stop_recording()
            else:
                k_events = []

            all_k_events = []
            all_k_events += getattr(self, "_paused_k_events", [])
            all_k_events += k_events

            filtered_k_events = [e for e in all_k_events if not (e.name == 'f10' and e.event_type in ('down', 'up'))]

            self.app.events = sorted(
                [{'type': 'keyboard', 'event': e.event_type, 'name': e.name, 'time': e.time} for e in filtered_k_events] +
                self._mouse_events,
                key=lambda e: e['time']
            )
            self.app.log(f"[{format_time(time.time())}] 錄製完成，共 {len(self.app.events)} 筆事件。")
            self.app.log(f"事件預覽: {json.dumps(self.app.events[:10], ensure_ascii=False, indent=2)}")
        except Exception as ex:
            try:
                self.app.log(f"[{format_time(time.time())}] 錄製執行緒發生錯誤: {ex}")
            except Exception:
                pass

    def toggle_pause(self):
        self.app.paused = not getattr(self.app, "paused", False)
        if self.app.paused:
            try: self.app.log(f"[{format_time(time.time())}] 已暫停。")
            except: pass
        else:
            try: self.app.log(f"[{format_time(time.time())}] 已繼續。")
            except: pass
        # 更新按鈕文字（若可用）
        try:
            lang_map = getattr(self.app, "LANG_MAP", None) or {}
            lm = lang_map.get(self.app.language_var.get(), lang_map.get("繁體中文", {}))
            text = lm.get("暫停/繼續", "暫停/繼續") + f" ({self.app.hotkey_map.get('pause','')})"
            self.app.btn_pause.config(text=text)
        except Exception:
            try:
                self.app.btn_pause.config(text=f"暫停/繼續 ({self.app.hotkey_map.get('pause','')})")
            except Exception:
                pass

    def stop_record(self):
        if getattr(self.app, "recording", False):
            self.app.recording = False
            try: self.app.log(f"[{format_time(time.time())}] 停止錄製。")
            except: pass
            self._wait_record_thread_finish()

    def _wait_record_thread_finish(self):
        if self._record_thread_handle and self._record_thread_handle.is_alive():
            self.app.after(100, self._wait_record_thread_finish)
        else:
            try:
                self.app.auto_save_script()
            except Exception:
                pass
