import threading
import time
import tkinter as tk
import win32api
import win32gui
import win32con
import mouse

class TargetWindowSelector:
    """
    提供一個輕量的 Toplevel 視窗來進行「選擇目標視窗」，
    並在背景執行一個監控執行緒以維護 app.selected_target 資訊。
    """

    def __init__(self, app):
        self.app = app
        self.win = None
        self._listening = False
        self._monitor_running = False
        self._monitor_thread = None

    def open(self):
        if self.win:
            try:
                self.win.lift()
                return
            except Exception:
                pass

        self.win = tk.Toplevel(self.app)
        self.win.title("選擇目標視窗")
        self.win.geometry("360x140")
        self.win.resizable(False, False)

        lbl = tk.Label(self.win, text="移動滑鼠至目標視窗並按左鍵以選取。\n視窗會在背景持續監控。", justify="left")
        lbl.pack(padx=12, pady=(12,6), anchor="w")

        self.info_label = tk.Label(self.win, text="目前游標: (?,?)\n視窗標題: None", justify="left", anchor="w")
        self.info_label.pack(padx=12, pady=(0,8), anchor="w")

        btn_frame = tk.Frame(self.win)
        btn_frame.pack(fill="x", padx=12, pady=(0,10))

        start_btn = tk.Button(btn_frame, text="開始選擇", command=self.start_listen, width=12)
        start_btn.pack(side="left")

        cancel_btn = tk.Button(btn_frame, text="關閉", command=self.close, width=12)
        cancel_btn.pack(side="right")

        # 每 120ms 更新游標位置與視窗資訊（即使未點選）
        self._update_ui_loop()

    def _update_ui_loop(self):
        if not self.win:
            return
        try:
            x, y = win32api.GetCursorPos()
            try:
                hwnd = win32gui.WindowFromPoint((x, y))
                title = win32gui.GetWindowText(hwnd)
                title = title if title else "<no title>"
            except Exception:
                hwnd = None
                title = "無"
            self.info_label.config(text=f"目前游標: ( {x} , {y} )\n視窗標題: {title}")
        except Exception:
            pass
        # 繼續更新
        try:
            self.win.after(120, self._update_ui_loop)
        except Exception:
            pass

    def start_listen(self):
        if self._listening:
            return
        self._listening = True
        threading.Thread(target=self._listen_click_thread, daemon=True).start()

    def _listen_click_thread(self):
        try:
            self.app.log("開始等待左鍵點擊以選取目標視窗...")
        except Exception:
            pass
        # 等待第一個左鍵點擊
        try:
            mouse.wait('left')  # 阻塞直到左鍵點擊
        except Exception:
            # 若 mouse 無法使用，嘗試使用簡單輪詢偵測按鍵（fallback）
            try:
                import ctypes
                user32 = ctypes.windll.user32
                while self._listening:
                    if user32.GetAsyncKeyState(0x01) & 0x8000:
                        break
                    time.sleep(0.05)
            except Exception:
                pass

        # 取得點擊時游標位置與視窗
        try:
            x, y = win32api.GetCursorPos()
            hwnd = win32gui.WindowFromPoint((x, y))
            title = win32gui.GetWindowText(hwnd)
            rect = win32gui.GetWindowRect(hwnd) if hwnd else None
            target = {"hwnd": int(hwnd) if hwnd else None, "title": title or "", "rect": rect, "screen_x": x, "screen_y": y}
            # 存回主 app
            self.app.selected_target = target
            # 如果希望在事件回放時自動使用此 hwnd，可儲存在 user_config 的欄位（只存 title 以便辨識）
            try:
                self.app.user_config["last_target_title"] = title or ""
                self.app.save_config()
            except Exception:
                pass
            try:
                self.app.log(f"[{time.strftime('%H:%M:%S')}] 已選擇目標視窗: ({hwnd}) {title}")
            except Exception:
                pass
            # 若尚未啟動背景監控，啟動一個守護 thread 以確認該視窗是否仍存在（若不存在嘗試以標題搜尋）
            if not self._monitor_running:
                self._monitor_running = True
                self._monitor_thread = threading.Thread(target=self._monitor_target_thread, daemon=True)
                self._monitor_thread.start()
        except Exception as e:
            try:
                self.app.log(f"選擇目標視窗失敗: {e}")
            except Exception:
                pass
        finally:
            self._listening = False

    def _monitor_target_thread(self):
        """
        背景監控：檢查 selected_target 的 hwnd 是否仍有效；若無效嘗試以標題重新尋找。
        監控頻率低，避免大量耗能。
        """
        while self._monitor_running:
            try:
                tgt = getattr(self.app, "selected_target", None)
                if not tgt:
                    time.sleep(2.0)
                    continue
                hwnd = tgt.get("hwnd")
                title = tgt.get("title", "")
                valid = False
                if hwnd:
                    try:
                        valid = bool(win32gui.IsWindow(hwnd))
                    except Exception:
                        valid = False
                if not valid and title:
                    # 嘗試以標題搜尋（精準匹配）
                    try:
                        found = win32gui.FindWindow(None, title)
                        if found:
                            self.app.selected_target["hwnd"] = int(found)
                            try:
                                self.app.log(f"背景監控：依標題重新找到視窗 hwnd={found}")
                            except Exception:
                                pass
                            valid = True
                    except Exception:
                        pass
                # 若視窗完全不存在，保留 title 但清除 hwnd
                if not valid:
                    self.app.selected_target["hwnd"] = None
                time.sleep(2.5)
            except Exception:
                time.sleep(2.5)
        # 結束監控
        self._monitor_running = False

    def stop(self):
        self._monitor_running = False
        self._listening = False
        try:
            if self.win:
                self.win.destroy()
        except Exception:
            pass
        self.win = None

    def close(self):
        self.stop()