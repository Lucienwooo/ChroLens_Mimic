
import os
import json
import datetime
from typing import Any, Dict, List

def _normalize_loaded(data: Any) -> Dict[str, Any]:
    """將載入資料轉成 dict 格式: {'events': [...], 'settings': {...}}"""
    if isinstance(data, dict) and "events" in data:
        events = data.get("events", []) or []
        # 優先從 settings 區塊讀取，若不存在則從根層級讀取（向下相容）
        if "settings" in data and isinstance(data["settings"], dict):
            settings = {
                "speed": data["settings"].get("speed", "100"),
                "repeat": data["settings"].get("repeat", "1"),
                "repeat_time": data["settings"].get("repeat_time", "00:00:00"),
                "repeat_interval": data["settings"].get("repeat_interval", "00:00:00"),
                "random_interval": data["settings"].get("random_interval", False),
                "script_hotkey": data["settings"].get("script_hotkey", ""),
                "script_actions": data["settings"].get("script_actions", []),
                "window_info": data["settings"].get("window_info", None)
            }
        else:
            # 向下相容：從根層級讀取
            settings = {
                "speed": data.get("speed", "100"),
                "repeat": data.get("repeat", "1"),
                "repeat_time": data.get("repeat_time", "00:00:00"),
                "repeat_interval": data.get("repeat_interval", "00:00:00"),
                "random_interval": data.get("random_interval", False),
                "script_hotkey": data.get("script_hotkey", ""),
                "script_actions": data.get("script_actions", []),
                "window_info": data.get("window_info", None)
            }
        return {"events": events, "settings": settings}
    else:
        # 舊格式：直接是事件 list
        return {"events": data or [], "settings": {
            "speed": "100", "repeat": "1", "repeat_time": "00:00:00",
            "repeat_interval": "00:00:00", "random_interval": False, "script_hotkey": ""
        }}

def load_script(path: str) -> Dict[str, Any]:
    """讀取腳本檔案並回傳 normalized dict"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _normalize_loaded(data)

def save_script(path: str, events: List[dict], settings: Dict[str, Any]) -> None:
    """儲存腳本（覆寫），使用 settings 區塊儲存所有參數"""
    data = {
        "events": events,
        "settings": {
            "speed": settings.get("speed", "100"),
            "repeat": settings.get("repeat", "1"),
            "repeat_time": settings.get("repeat_time", "00:00:00"),
            "repeat_interval": settings.get("repeat_interval", "00:00:00"),
            "random_interval": settings.get("random_interval", False),
            "script_hotkey": settings.get("script_hotkey", ""),
            "script_actions": settings.get("script_actions", []),
            "window_info": settings.get("window_info", None)
        }
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def auto_save_script(script_dir: str, events: List[dict], settings: Dict[str, Any]) -> str:
    """自動存檔：在 script_dir 建立 timestamp 檔名，回傳檔名"""
    if not os.path.exists(script_dir):
        os.makedirs(script_dir)
    ts = datetime.datetime.now().strftime("%Y_%m%d_%H%M_%S")
    filename = f"{ts}.json"
    path = os.path.join(script_dir, filename)
    save_script(path, events, settings)
    return filename

def save_script_settings(path: str, settings: Dict[str, Any]) -> None:
    """只更新腳本內的設定欄位（使用 settings 區塊儲存）"""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 轉換為新格式（events + settings）
    if not (isinstance(data, dict) and "events" in data):
        data = {"events": data, "settings": {}}
    
    # 確保有 settings 區塊
    if "settings" not in data:
        data["settings"] = {}
    
    # 更新 settings 區塊中的參數
    data["settings"].update({
        "speed": settings.get("speed", data["settings"].get("speed", "100")),
        "repeat": settings.get("repeat", data["settings"].get("repeat", "1")),
        "repeat_time": settings.get("repeat_time", data["settings"].get("repeat_time", "00:00:00")),
        "repeat_interval": settings.get("repeat_interval", data["settings"].get("repeat_interval", "00:00:00")),
        "random_interval": settings.get("random_interval", data["settings"].get("random_interval", False)),
        "script_hotkey": settings.get("script_hotkey", data["settings"].get("script_hotkey", "")),
        "script_actions": settings.get("script_actions", data["settings"].get("script_actions", [])),
        "window_info": settings.get("window_info", data["settings"].get("window_info", None))
    })
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
