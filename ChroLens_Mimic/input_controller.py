import ctypes
import win32gui, pywintypes, win32con

def show_error_window(window_name):
    ctypes.windll.user32.MessageBoxW(0, f'找不到 \"{window_name}\" 視窗，請重試', '錯誤', 0x10)

def client_to_screen(hwnd, rel_x, rel_y, window_name=""):
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return left + rel_x, top + rel_y
    except pywintypes.error:
        ctypes.windll.user32.MessageBoxW(0, f'找不到 \"{window_name}\" 視窗，請重試', '錯誤', 0x10)
        raise

def screen_to_client(hwnd, x, y):
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return x - left, y - top

def move_mouse_abs(x, y):
    ctypes.windll.user32.SetCursorPos(int(x), int(y))

def mouse_event_win(event, x=0, y=0, button='left', delta=0):
    user32 = ctypes.windll.user32
    if event in ('down','up'):
        flags = {'left': (0x0002, 0x0004), 'right': (0x0008, 0x0010), 'middle': (0x0020, 0x0040)}
        flag = flags.get(button, (0x0002,0x0004))[0 if event=='down' else 1]
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [("dx", ctypes.c_long),("dy", ctypes.c_long),("mouseData", ctypes.c_ulong),("dwFlags", ctypes.c_ulong),("time", ctypes.c_ulong),("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
        class INPUT(ctypes.Structure):
            _fields_ = [("type", ctypes.c_ulong),("mi", MOUSEINPUT)]
        inp = INPUT()
        inp.type = 0
        inp.mi = MOUSEINPUT(0,0,0,flag,0,None)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    elif event == 'wheel':
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [("dx", ctypes.c_long),("dy", ctypes.c_long),("mouseData", ctypes.c_ulong),("dwFlags", ctypes.c_ulong),("time", ctypes.c_ulong),("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
        class INPUT(ctypes.Structure):
            _fields_ = [("type", ctypes.c_ulong),("mi", MOUSEINPUT)]
        inp = INPUT()
        inp.type = 0
        inp.mi = MOUSEINPUT(0,0,int(delta*120),0x0800,0,None)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))