import os
import json
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from recorder import Recorder
from input_controller import show_error_window

CONFIG_FILE = "user_config.json"
SCRIPTS_DIR = "scripts"
LAST_SCRIPT_FILE = "last_script.txt"

LANG_MAP = {
    "繁體中文": {
        "開始錄製": "開始錄製", "暫停/繼續": "暫停/繼續", "停止": "停止", "回放": "回放",
        "回放速度:": "回放速度:", "儲存": "儲存", "Language": "Language"
    },
    "日本語": {
        "開始錄製": "録画開始", "暫停/繼続": "一時停止 / 再開", "停止": "停止", "回放": "再生",
        "回放速度:": "再生速度：", "儲存": "保存", "Language": "言語"
    },
    "English": {
        "開始錄製": "Start Recording", "暫停/繼續": "Pause/Resume", "停止": "Stop", "回放": "Play",
        "回放速度:": "Playback Speed:", "儲存": "Save", "Language": "Language"
    }
}

def load_user_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"skin": "darkly", "last_script": "", "repeat": "1", "speed": "100", "script_dir": SCRIPTS_DIR, "language": "繁體中文", "hotkey_map": {"start":"F10","pause":"F11","stop":"F9","play":"F12","tiny":"alt+`"}}

def save_user_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)
    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, background="#ffffe0", relief="solid", borderwidth=1, font=("Microsoft JhengHei", 10))
        label.pack(ipadx=6, ipady=2)
    def hide_tip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

class RecorderApp(tb.Window):
    def __init__(self):
        self.user_config = load_user_config()
        skin = self.user_config.get("skin", "darkly")
        lang = self.user_config.get("language", "繁體中文")
        super().__init__(themename=skin)
        self.title("ChroLens_Mimic_2.6")
        self.geometry("760x520")

        # ensure script dir
        self.script_dir = self.user_config.get("script_dir", SCRIPTS_DIR)
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)

        # UI variables
        self.language_var = tk.StringVar(self, value=lang)
        self.speed_var = tk.StringVar(self, value=self.user_config.get("speed","100"))
        self.repeat_var = tk.StringVar(self, value=self.user_config.get("repeat","1"))

        # Top buttons
        frm_top = tb.Frame(self, padding=8)
        frm_top.pack(fill="x")
        self.btn_start = tb.Button(frm_top, text=LANG_MAP[lang]["開始錄製"], bootstyle="primary", command=self._on_start)
        self.btn_start.grid(row=0, column=0, padx=4)
        self.btn_pause = tb.Button(frm_top, text=LANG_MAP[lang]["暫停/繼續"], bootstyle="info", command=self._on_pause)
        self.btn_pause.grid(row=0, column=1, padx=4)
        self.btn_stop = tb.Button(frm_top, text=LANG_MAP[lang]["停止"], bootstyle="warning", command=self._on_stop)
        self.btn_stop.grid(row=0, column=2, padx=4)
        self.btn_play = tb.Button(frm_top, text=LANG_MAP[lang]["回放"], bootstyle="success", command=self._on_play)
        self.btn_play.grid(row=0, column=3, padx=4)

        # controls row
        frm_ctl = tb.Frame(self, padding=6)
        frm_ctl.pack(fill="x")
        tb.Label(frm_ctl, text=LANG_MAP[lang]["回放速度:"]).grid(row=0, column=0, sticky="w")
        self.speed_entry = tb.Entry(frm_ctl, textvariable=self.speed_var, width=6)
        self.speed_entry.grid(row=0, column=1, padx=6)

        # language selector
        tb.Label(frm_ctl, text=LANG_MAP[lang]["Language"]).grid(row=0, column=4, sticky="e")
        self.lang_combo = tb.Combobox(frm_ctl, values=list(LANG_MAP.keys()), textvariable=self.language_var, width=10)
        self.lang_combo.grid(row=0, column=5, padx=6)
        self.lang_combo.bind("<<ComboboxSelected>>", self.change_language)

        # log area
        self.log_text = tb.Text(self, height=22, state="disabled", font=("Microsoft JhengHei", 10))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=6)

        # Recorder
        self.recorder = Recorder(
            log_callback=self.log,
            get_script_dir=lambda: self.script_dir,
            on_update_time=self.update_time_label,
            on_update_countdown=self.update_countdown_label,
            on_update_total_time=self.update_total_time_label
        )

        # load last script asynchronously
        self.after(600, self.load_last_script)

    def change_language(self, event=None):
        lang = self.language_var.get()
        self.user_config["language"] = lang
        save_user_config(self.user_config)
        # update button texts (simple)
        self.btn_start.config(text=LANG_MAP[lang]["開始錄製"])
        self.btn_pause.config(text=LANG_MAP[lang]["暫停/繼續"])
        self.btn_stop.config(text=LANG_MAP[lang]["停止"])
        self.btn_play.config(text=LANG_MAP[lang]["回放"])

    def log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def update_time_label(self, seconds):
        # show brief info in log
        self.log(f"[時間] {seconds:.2f}s")

    def update_countdown_label(self, seconds):
        self.log(f"[倒數] {int(seconds)}s")

    def update_total_time_label(self, seconds):
        self.log(f"[總剩餘] {int(seconds)}s")

    def _on_start(self):
        try:
            self.recorder.start_record()
        except Exception as e:
            self.log(f"Start error: {e}")

    def _on_pause(self):
        self.recorder.toggle_pause()

    def _on_stop(self):
        self.recorder.stop_all()

    def _on_play(self):
        try:
            speed = max(1.0, float(self.speed_var.get())/100.0) if self.speed_var.get() else 1.0
        except Exception:
            speed = 1.0
        self.recorder.play_record(speed=speed, repeat=int(self.repeat_var.get() or 1))

    def load_last_script(self):
        if os.path.exists(LAST_SCRIPT_FILE):
            try:
                with open(LAST_SCRIPT_FILE, "r", encoding="utf-8") as f:
                    last = f.read().strip()
                if last:
                    path = os.path.join(self.script_dir, last)
                    if os.path.exists(path):
                        self.recorder.load_script(path)
                        self.log(f"已載入上次腳本 {last}")
            except Exception:
                pass

    def save_user_config(self):
        save_user_config(self.user_config)