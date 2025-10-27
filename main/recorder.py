# recorder.py
import time
import threading
import json

class Recorder:
    """
    Core recording / playback logic.
    UI code should call start_record/stop_record/toggle_pause/play etc.
    This is a minimal scaffold — 可逐步把原 ui.py 中的細節搬入。
    """
    def __init__(self, logger=None, mouse_controller=None, keyboard_module=None):
        self.logger = logger or (lambda s: None)
        self.mouse = mouse_controller
        self.keyboard = keyboard_module
        self.recording = False
        self.playing = False
        self.paused = False
        self.events = []
        self._record_thread = None
        self._play_thread = None
        self._record_start_time = None

    def start_record(self):
        if self.recording:
            return
        self.recording = True
        self.paused = False
        self.events = []
        self._record_start_time = time.time()
        self.logger(f"[{time.ctime()}] Recorder.start_record()")
        self._record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self._record_thread.start()

    def _record_loop(self):
        # TODO: 把原 ui.py 的 mouse/keyboard listener 邏輯搬過來
        # 目前僅做 time-stamp 範例事件
        while self.recording:
            if not self.paused:
                self.events.append({'type': 'noop', 'time': time.time()})
            time.sleep(0.1)
        self.logger(f"[{time.ctime()}] Recorder._record_loop finished; {len(self.events)} events recorded")

    def stop_record(self):
        if not self.recording:
            return
        self.recording = False
        if self._record_thread and self._record_thread.is_alive():
            self._record_thread.join(timeout=0.5)

    def toggle_pause(self):
        self.paused = not self.paused
        self.logger(f"[{time.ctime()}] Recorder.pause -> {self.paused}")

    def play(self, speed=1.0, repeat=1, on_event=None):
        if self.playing:
            return
        self.playing = True
        self.paused = False
        self._play_thread = threading.Thread(target=self._play_loop, args=(speed, repeat, on_event), daemon=True)
        self._play_thread.start()

    def _play_loop(self, speed, repeat, on_event):
        try:
            for r in range(max(1, repeat)):
                if not self.playing:
                    break
                base = self.events[0]['time'] if self.events else time.time()
                for e in self.events:
                    if not self.playing:
                        break
                    while self.paused:
                        time.sleep(0.05)
                    offset = (e['time'] - base) / max(1e-6, speed)
                    target = time.time() + offset
                    while time.time() < target and self.playing and not self.paused:
                        time.sleep(0.01)
                    if not self.playing:
                        break
                    # call back to UI or hotkey manager for real action
                    if on_event:
                        try:
                            on_event(e)
                        except Exception:
                            pass
            self.logger(f"[{time.ctime()}] Recorder finished play")
        finally:
            self.playing = False
            self.paused = False

    def stop_play(self):
        self.playing = False