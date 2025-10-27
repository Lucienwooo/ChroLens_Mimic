# hotkeys.py
import keyboard

class HotkeyManager:
    def __init__(self, logger=None):
        self._handlers = {}
        self.logger = logger or (lambda s: None)

    def register(self, name, hotkey, callback, suppress=False):
        try:
            handler = keyboard.add_hotkey(hotkey, callback, suppress=suppress, trigger_on_release=False)
            self._handlers[name] = handler
            self.logger(f"HotkeyManager: registered {hotkey} -> {name}")
        except Exception as e:
            self.logger(f"HotkeyManager.register failed: {e}")

    def unregister(self, name):
        if name in self._handlers:
            try:
                keyboard.remove_hotkey(self._handlers[name])
            except Exception:
                pass
            del self._handlers[name]

    def unregister_all(self):
        for name in list(self._handlers.keys()):
            self.unregister(name)