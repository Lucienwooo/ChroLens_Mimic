import argparse
import time
import win32gui
import win32con
import win32api
import ctypes

def enum_windows():
    wins = []
    def cb(hwnd, lParam):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            wins.append((hwnd, win32gui.GetWindowText(hwnd)))
        return True
    win32gui.EnumWindows(cb, None)
    return wins

def find_window(title, partial=True):
    if not title:
        return None
    for hwnd, txt in enum_windows():
        if (partial and title.lower() in txt.lower()) or (not partial and title == txt):
            return hwnd
    return None

def screen_to_client(hwnd, x, y):
    pt = win32gui.ScreenToClient(hwnd, (int(x), int(y)))
    return pt

def lparam_from_xy(x, y):
    return int(x) | (int(y) << 16)

def post_mouse_click(hwnd, x, y, button="left", screen_coords=False):
    if screen_coords:
        x, y = screen_to_client(hwnd, x, y)
    lparam = lparam_from_xy(x, y)
    if button == "left":
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
        time.sleep(0.02)
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
    elif button == "right":
        win32gui.PostMessage(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lparam)
        time.sleep(0.02)
        win32gui.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, lparam)
    else:
        # middle
        win32gui.PostMessage(hwnd, win32con.WM_MBUTTONDOWN, win32con.MK_MBUTTON, lparam)
        time.sleep(0.02)
        win32gui.PostMessage(hwnd, win32con.WM_MBUTTONUP, 0, lparam)

def send_text_to_edit(hwnd, text):
    # 嘗試找 Edit control（常見於標準視窗），用 WM_SETTEXT
    child = win32gui.FindWindowEx(hwnd, 0, "Edit", None)
    if child:
        win32gui.SendMessage(child, win32con.WM_SETTEXT, 0, text)
        return True
    # 若找不到 edit，嘗試發 WM_CHAR 給目標視窗（可能被忽略）
    for ch in text:
        vk = win32api.VkKeyScan(ch) & 0xff
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
        win32gui.PostMessage(hwnd, win32con.WM_CHAR, ord(ch), 0)
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0)
    return True

def post_key_press(hwnd, key, repeat=1):
    # 支援單字母/數字或常見字符串如 'enter','tab','esc'
    key_map = {
        "enter": win32con.VK_RETURN,
        "tab": win32con.VK_TAB,
        "esc": win32con.VK_ESCAPE,
        "space": win32con.VK_SPACE,
        "back": win32con.VK_BACK,
    }
    vk = key_map.get(key.lower())
    if vk is None:
        if len(key) == 1:
            vk = ord(key.upper())
        else:
            try:
                vk = int(key, 0)
            except Exception:
                vk = None
    if vk is None:
        raise ValueError("Unknown key")
    for _ in range(repeat):
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
        time.sleep(0.02)
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0)
        time.sleep(0.02)

def bring_to_front(hwnd):
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass

def main():
    p = argparse.ArgumentParser(description="background sender: send mouse/keys to target window")
    p.add_argument("--title", "-t", required=True, help="target window title (partial match)")
    p.add_argument("--partial", action="store_true", default=True, help="use partial match (default)")
    p.add_argument("--click", nargs=2, type=int, metavar=('X','Y'), help="click at client coords (or use --screen)")
    p.add_argument("--button", choices=("left","right","middle"), default="left", help="mouse button")
    p.add_argument("--screen", action="store_true", help="treat click coords as screen coords")
    p.add_argument("--text", help="send text (tries WM_SETTEXT to Edit control, else sends WM_CHAR)")
    p.add_argument("--key", help="send key (e.g. 'a','enter','tab')")
    p.add_argument("--bring", action="store_true", help="restore & bring window to front before actions")
    args = p.parse_args()

    hwnd = find_window(args.title, partial=args.partial)
    if not hwnd:
        print("找不到視窗，請確認標題。")
        return

    print(f"目標 hwnd={hwnd}, title='{win32gui.GetWindowText(hwnd)}'")

    if args.bring:
        bring_to_front(hwnd)
        time.sleep(0.15)

    if args.click:
        x, y = args.click
        post_mouse_click(hwnd, x, y, button=args.button, screen_coords=args.screen)
        print(f"已發送 {args.button} click to ({x},{y}), screen={args.screen}")

    if args.text:
        send_text_to_edit(hwnd, args.text)
        print("已發送 text")

    if args.key:
        post_key_press(hwnd, args.key)
        print(f"已發送 key {args.key}")

if __name__ == "__main__":
    main()