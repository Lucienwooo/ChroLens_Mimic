# scripts.py
import os
import json
import datetime

class ScriptManager:
    def __init__(self, scripts_dir="scripts", logger=None):
        self.scripts_dir = scripts_dir
        self.logger = logger or (lambda s: None)
        if not os.path.exists(self.scripts_dir):
            os.makedirs(self.scripts_dir)

    def list_scripts(self):
        return sorted([f for f in os.listdir(self.scripts_dir) if f.endswith(".json")])

    def load(self, name):
        path = os.path.join(self.scripts_dir, name)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, name, data):
        path = os.path.join(self.scripts_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.logger(f"ScriptManager.save: saved {name}")

    def rename(self, old, new):
        oldp = os.path.join(self.scripts_dir, old)
        newp = os.path.join(self.scripts_dir, new)
        os.rename(oldp, newp)
        self.logger(f"ScriptManager.rename: {old} -> {new}")

    def delete(self, name):
        path = os.path.join(self.scripts_dir, name)
        os.remove(path)
        self.logger(f"ScriptManager.delete: removed {name}")

    def auto_save(self, events, meta=None):
        ts = datetime.datetime.now().strftime("%Y_%m%d_%H%M_%S.json")
        data = {"events": events}
        if meta:
            data.update(meta)
        self.save(ts, data)
        return ts