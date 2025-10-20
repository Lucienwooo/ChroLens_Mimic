import json
import os

USER_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "user_config.json")
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")
LAST_SCRIPT_FILE = os.path.join(os.path.dirname(__file__), "last_script.txt")
MOUSE_SAMPLE_INTERVAL = 0.02  # 如果 recorder_app.py 依賴此常數，可放在這裡

DEFAULT_USER_CONFIG = {
    "skin": "darkly",
    "language": "繁體中文",
    "hotkey_map": {
        "start": "F10",
        "pause": "F11",
        "stop": "F9",
        "play": "F12",
        "tiny": "alt+`"
    },
    "speed": "100",
    "repeat": "1",
    "script_dir": SCRIPTS_DIR,
    "last_script": ""
}

def load_user_config():
    try:
        if not os.path.exists(USER_CONFIG_FILE):
            # 建立預設檔
            os.makedirs(os.path.dirname(USER_CONFIG_FILE), exist_ok=True)
            with open(USER_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_USER_CONFIG, f, ensure_ascii=False, indent=2)
            return dict(DEFAULT_USER_CONFIG)
        with open(USER_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return dict(DEFAULT_USER_CONFIG)
            # 合併預設值（若缺某些鍵）
            merged = dict(DEFAULT_USER_CONFIG)
            merged.update(data)
            # 確保 script_dir 存在
            if not os.path.exists(merged.get("script_dir", SCRIPTS_DIR)):
                try:
                    os.makedirs(merged.get("script_dir", SCRIPTS_DIR), exist_ok=True)
                except Exception:
                    pass
            return merged
    except Exception:
        # 若解析失敗，回傳預設並覆寫檔案以修復
        try:
            with open(USER_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_USER_CONFIG, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return dict(DEFAULT_USER_CONFIG)

def save_user_config(cfg):
    try:
        os.makedirs(os.path.dirname(USER_CONFIG_FILE), exist_ok=True)
        with open(USER_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False