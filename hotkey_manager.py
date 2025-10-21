import keyboard

class HotkeyManager:
    def __init__(self, app):
        self.app = app
        self._handlers = {}

    def register_all(self, hotkey_map):
        self.remove_all()
        for key, hk in hotkey_map.items():
            try:
                target = getattr(self.app, {"start":"start_record","pause":"toggle_pause","stop":"stop_all","play":"play_record","mini":"toggle_mini_mode"}[key])
                h = keyboard.add_hotkey(hk, target, suppress=False, trigger_on_release=False)
                self._handlers[key] = h
                try: self.app.log(f"已註冊快捷鍵: {hk} → {key}")
                except: pass
            except Exception as e:
                try: self.app.log(f"快捷鍵 {hk} 註冊失敗: {e}")
                except: pass

    def remove_all(self):
        for h in list(self._handlers.values()):
            try:
                keyboard.remove_hotkey(h)
            except Exception:
                pass
        self._handlers.clear()