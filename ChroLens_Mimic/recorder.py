import threading
import time
import json
import os
import datetime
import random

try:
    import keyboard
except Exception:
    keyboard = None

from input_controller import move_mouse_abs, mouse_event_win

class Recorder:
    def __init__(self, log_callback=print, get_script_dir=lambda: "scripts",
                 on_update_time=lambda s: None, on_update_countdown=lambda s: None, on_update_total_time=lambda s: None):
        self.log = log_callback
        self.get_script_dir = get_script_dir
        self.on_update_time = on_update_time
        self.on_update_countdown = on_update_countdown
        self.on_update_total_time = on_update_total_time

        self.recording = False
        self.playing = False
        self.paused = False
        self.events = []
        self._record_thread_handle = None
        self._play_thread_handle = None

    def _format_time(self, ts):
        return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")

    def start_record(self):
        if self.recording:
            return
        self.events = []
        self.recording = True
        self.paused = False
        self._record_start_time = time.time()
        self.log(f"[{self._format_time(time.time())}] 開始錄製...")
        self._record_thread_handle = threading.Thread(target=self._record_thread, daemon=True)
        self._record_thread_handle.start()
        threading.Thread(target=self._record_time_updater, daemon=True).start()
        # start keyboard recording if available
        if keyboard:
            try:
                keyboard.start_recording()
            except Exception:
                pass

    def _record_time_updater(self):
        while self.recording:
            self.on_update_time(time.time() - self._record_start_time)
            time.sleep(0.2)
        self.on_update_time(0)

    def _record_thread(self):
        try:
            # use pynput for mouse capture
            from pynput.mouse import Listener as MouseListener, Controller as MouseController
            from pynput import keyboard as pkeyboard

            mouse_ctrl = MouseController()
            last_pos = mouse_ctrl.position
            mouse_events = []

            def on_click(x, y, button, pressed):
                if self.recording and not self.paused:
                    mouse_events.append({'type':'mouse','event': 'down' if pressed else 'up','button':str(button).replace('Button.',''),'x':x,'y':y,'time':time.time()})

            def on_scroll(x, y, dx, dy):
                if self.recording and not self.paused:
                    mouse_events.append({'type':'mouse','event':'wheel','delta':dy,'x':x,'y':y,'time':time.time()})

            listener = MouseListener(on_click=on_click, on_scroll=on_scroll)
            listener.start()

            # sample movement
            mouse_events.append({'type':'mouse','event':'move','x':last_pos[0],'y':last_pos[1],'time':time.time()})
            while self.recording:
                pos = mouse_ctrl.position
                if pos != last_pos and not self.paused:
                    mouse_events.append({'type':'mouse','event':'move','x':pos[0],'y':pos[1],'time':time.time()})
                    last_pos = pos
                time.sleep(0.01)
            listener.stop()

            # keyboard events
            klist = []
            if keyboard:
                try:
                    k_events = keyboard.stop_recording()
                    for e in k_events:
                        # keyboard library event has attributes: name, event_type, time
                        klist.append({'type':'keyboard','event': getattr(e,'event_type', None), 'name': getattr(e,'name', None), 'time': getattr(e,'time', time.time())})
                except Exception:
                    pass

            all_events = klist + mouse_events
            self.events = sorted(all_events, key=lambda e: e.get('time', time.time()))
            self.log(f"[{self._format_time(time.time())}] 錄製完成，共 {len(self.events)} 筆事件。")
        except Exception as ex:
            self.log(f"錄製執行緒發生錯誤: {ex}")
        finally:
            self.recording = False

    def stop_all(self):
        stopped = False
        if self.recording:
            self.recording = False
            stopped = True
            self.log(f"[{self._format_time(time.time())}] 停止錄製。")
        if self.playing:
            self.playing = False
            stopped = True
            self.log(f"[{self._format_time(time.time())}] 停止回放。")
        if not stopped:
            self.log(f"[{self._format_time(time.time())}] 無進行中動作可停止。")

    def toggle_pause(self):
        if self.recording or self.playing:
            self.paused = not self.paused
            state = "暫停" if self.paused else "繼續"
            mode = "錄製" if self.recording else "回放"
            self.log(f"[{self._format_time(time.time())}] {mode}{state}。")

    def play_record(self, speed=1.0, repeat=1, repeat_interval=0, random_interval=False, repeat_time_limit=None):
        if self.playing:
            return
        if not self.events:
            self.log("沒有可回放的事件，請先錄製或載入腳本。")
            return
        self.playing = True
        self.paused = False
        self._play_thread_handle = threading.Thread(target=self._play_thread, kwargs={
            "speed":speed,"repeat":repeat,"repeat_interval":repeat_interval,"random_interval":random_interval,"repeat_time_limit":repeat_time_limit
        }, daemon=True)
        self._play_thread_handle.start()
        threading.Thread(target=self._play_time_updater, daemon=True).start()

    def _play_time_updater(self):
        while self.playing:
            # placeholder for UI callbacks
            self.on_update_total_time(0)
            time.sleep(0.5)
        self.on_update_total_time(0)

    def _play_thread(self, speed=1.0, repeat=1, repeat_interval=0, random_interval=False, repeat_time_limit=None):
        try:
            base_events = self.events
            if not base_events:
                return
            base_start = base_events[0]['time']
            total_duration = (base_events[-1]['time'] - base_start) / (speed if speed>0 else 1)
            count = 0
            infinite = repeat <= 0
            while self.playing and (infinite or count < repeat):
                play_start_wall = time.time()
                for e in base_events:
                    if not self.playing:
                        break
                    target_offset = (e['time'] - base_start) / (speed if speed>0 else 1)
                    target_time = play_start_wall + target_offset
                    while time.time() < target_time and self.playing:
                        if self.paused:
                            time.sleep(0.05)
                            continue
                        time.sleep(0.003)
                    if not self.playing:
                        break
                    # handle event
                    if e['type'] == 'mouse':
                        ev = e.get('event')
                        x = e.get('x',0); y = e.get('y',0)
                        if ev == 'move':
                            move_mouse_abs(x,y)
                        elif ev == 'down':
                            move_mouse_abs(x,y)
                            mouse_event_win('down', button=e.get('button','left'))
                        elif ev == 'up':
                            move_mouse_abs(x,y)
                            mouse_event_win('up', button=e.get('button','left'))
                        elif ev == 'wheel':
                            mouse_event_win('wheel', delta=e.get('delta',0))
                    elif e['type'] == 'keyboard' and e.get('name'):
                        try:
                            import keyboard as kb
                            if e.get('event') == 'down':
                                kb.press(e.get('name'))
                            elif e.get('event') == 'up':
                                kb.release(e.get('name'))
                        except Exception:
                            pass
                count += 1
                if (count < repeat or infinite) and self.playing:
                    sec = 0
                    if repeat_interval > 0:
                        sec = random.randint(1, repeat_interval) if random_interval else repeat_interval
                    t0 = time.time()
                    while self.playing and time.time()-t0 < sec:
                        if self.paused:
                            time.sleep(0.05)
                            continue
                        time.sleep(0.05)
        except Exception as ex:
            self.log(f"回放執行緒發生錯誤: {ex}")
        finally:
            self.playing = False
            self.paused = False
            self.log(f"[{self._format_time(time.time())}] 回放結束。")

    def save_script(self, filename=None):
        if not filename:
            filename = datetime.datetime.now().strftime("%Y_%m%d_%H%M_%S") + ".json"
        path = os.path.join(self.get_script_dir(), filename)
        data = {"events": self.events}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        try:
            with open("last_script.txt", "w", encoding="utf-8") as f:
                f.write(filename)
        except Exception:
            pass
        self.log(f"已儲存腳本 {filename}")

    def load_script(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "events" in data:
                self.events = data["events"]
            else:
                self.events = data
            self.log(f"已載入腳本 {os.path.basename(path)} 共 {len(self.events)} 筆事件。")
        except Exception as ex:
            self.log(f"載入腳本失敗: {ex}")