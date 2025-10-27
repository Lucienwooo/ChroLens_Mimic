import threading, time, os
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    _HAVE_WATCHDOG = True
except Exception:
    Observer = None
    FileSystemEventHandler = object
    _HAVE_WATCHDOG = False

class _Handler(FileSystemEventHandler):
    def __init__(self, cb, app):
        super().__init__()
        self.cb = cb
        self.app = app
    def on_any_event(self, event):
        if event.is_directory: return
        try:
            self.app.after(80, self.cb)
        except Exception:
            pass

class ScriptWatcher:
    def __init__(self, app):
        self.app = app
        self._observer = None
        self._poller = None
        self._stop = False

    def start(self, path, callback):
        self.stop()
        if not os.path.exists(path):
            os.makedirs(path)
        if _HAVE_WATCHDOG and Observer is not None:
            try:
                handler = _Handler(callback, self.app)
                obs = Observer()
                obs.schedule(handler, path, recursive=False)
                obs.start()
                self._observer = obs
                try: self.app.log("已啟動 watchdog 監視腳本目錄。")
                except: pass
                return
            except Exception as e:
                try: self.app.log(f"watchdog 啟動失敗: {e}")
                except: pass
        # fallback poller
        self._stop = False
        def poll():
            snapshot = set([f for f in os.listdir(path) if f.endswith('.json')])
            while not self._stop:
                try:
                    now = set([f for f in os.listdir(path) if f.endswith('.json')])
                    if now != snapshot:
                        snapshot = now
                        try: self.app.after(80, callback)
                        except: pass
                    time.sleep(1.0)
                except Exception:
                    time.sleep(1.0)
        self._poller = threading.Thread(target=poll, daemon=True)
        self._poller.start()
        try: self.app.log("已啟動 poller 監視腳本目錄（備援）。")
        except: pass

    def stop(self):
        try:
            if self._observer:
                self._observer.stop(); self._observer.join(timeout=1)
                self._observer = None
        except Exception:
            pass
        try:
            self._stop = True
            if self._poller and self._poller.is_alive():
                self._poller.join(timeout=0.5)
            self._poller = None
        except Exception:
            pass