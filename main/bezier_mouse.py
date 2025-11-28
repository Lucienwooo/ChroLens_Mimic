"""
BezierMouse - 貝茲曲線滑鼠移動
實現擬真的滑鼠移動軌跡，避免機械式的直線移動

特性：
- 二次/三次貝茲曲線軌跡
- 隨機控制點（每次移動路徑不同）
- Ease-in/Ease-out 速度變化（模擬人類加減速）
- 可調參數（移動時間、曲線彎曲度）

使用方式:
    from bezier_mouse import BezierMouseMover
    
    mover = BezierMouseMover()
    mover.move_to(500, 300, duration=0.5)  # 0.5秒移動到 (500, 300)
"""

import math
import time
import random
import ctypes
from typing import Tuple, List, Callable, Optional


class BezierMouseMover:
    """貝茲曲線滑鼠移動器
    
    實現人類化的滑鼠移動軌跡：
    1. 使用貝茲曲線生成平滑路徑
    2. 隨機控制點（避免固定軌跡）
    3. 速度變化（Ease-in/Ease-out）
    """
    
    def __init__(self, move_function: Optional[Callable[[int, int], None]] = None):
        """初始化移動器
        
        Args:
            move_function: 滑鼠移動函式，預設使用 Windows API
                           簽名: move_function(x: int, y: int) -> None
        """
        self.move_function = move_function or self._default_move
    
    def _default_move(self, x: int, y: int) -> None:
        """預設滑鼠移動（使用 Windows API）"""
        ctypes.windll.user32.SetCursorPos(int(x), int(y))
    
    def get_current_position(self) -> Tuple[int, int]:
        """取得當前滑鼠位置"""
        point = ctypes.wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
        return point.x, point.y
    
    def move_to(
        self,
        target_x: int,
        target_y: int,
        duration: float = 0.3,
        curve_type: str = "quadratic",
        randomness: float = 0.3,
        easing: str = "ease_in_out"
    ) -> None:
        """移動滑鼠到目標位置（使用貝茲曲線）
        
        Args:
            target_x: 目標 X 座標
            target_y: 目標 Y 座標
            duration: 移動持續時間（秒），建議 0.2~1.0
            curve_type: 曲線類型
                - "linear": 直線移動（無曲線）
                - "quadratic": 二次貝茲曲線（2個控制點）
                - "cubic": 三次貝茲曲線（3個控制點，更自然）
            randomness: 隨機程度 (0.0~1.0)
                - 0.0: 固定路徑
                - 0.3: 輕微隨機（推薦）
                - 1.0: 極度隨機（可能偏離較遠）
            easing: 速度變化曲線
                - "linear": 等速移動
                - "ease_in": 慢速啟動
                - "ease_out": 慢速結束
                - "ease_in_out": 慢速啟動與結束（推薦）
        """
        # 取得起點
        start_x, start_y = self.get_current_position()
        
        # 計算距離（若距離太近則直接移動）
        distance = math.sqrt((target_x - start_x)**2 + (target_y - start_y)**2)
        if distance < 5:
            self.move_function(target_x, target_y)
            return
        
        # 生成貝茲曲線路徑
        if curve_type == "linear":
            path = self._linear_path(start_x, start_y, target_x, target_y)
        elif curve_type == "quadratic":
            path = self._quadratic_bezier(start_x, start_y, target_x, target_y, randomness)
        elif curve_type == "cubic":
            path = self._cubic_bezier(start_x, start_y, target_x, target_y, randomness)
        else:
            raise ValueError(f"未知的曲線類型: {curve_type}")
        
        # 沿著路徑移動
        self._follow_path(path, duration, easing)
    
    def _linear_path(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        steps: int = 50
    ) -> List[Tuple[int, int]]:
        """生成直線路徑"""
        path = []
        for i in range(steps + 1):
            t = i / steps
            x = start_x + (end_x - start_x) * t
            y = start_y + (end_y - start_y) * t
            path.append((int(x), int(y)))
        return path
    
    def _quadratic_bezier(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        randomness: float,
        steps: int = 50
    ) -> List[Tuple[int, int]]:
        """生成二次貝茲曲線路徑（2個控制點）
        
        公式: B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
        """
        # 計算中點作為控制點基準
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        
        # 計算垂直偏移（讓曲線彎曲）
        distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        offset = distance * randomness * random.uniform(0.2, 0.5)
        
        # 隨機方向偏移
        angle = math.atan2(end_y - start_y, end_x - start_x) + math.pi / 2
        control_x = mid_x + offset * math.cos(angle) * random.choice([-1, 1])
        control_y = mid_y + offset * math.sin(angle) * random.choice([-1, 1])
        
        # 生成路徑
        path = []
        for i in range(steps + 1):
            t = i / steps
            # 二次貝茲曲線公式
            x = (1 - t)**2 * start_x + 2 * (1 - t) * t * control_x + t**2 * end_x
            y = (1 - t)**2 * start_y + 2 * (1 - t) * t * control_y + t**2 * end_y
            path.append((int(x), int(y)))
        return path
    
    def _cubic_bezier(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        randomness: float,
        steps: int = 50
    ) -> List[Tuple[int, int]]:
        """生成三次貝茲曲線路徑（3個控制點）
        
        公式: B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
        """
        # 計算兩個控制點
        distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        
        # 第一個控制點（接近起點）
        offset1 = distance * randomness * random.uniform(0.2, 0.4)
        angle1 = math.atan2(end_y - start_y, end_x - start_x) + random.uniform(-0.5, 0.5)
        control1_x = start_x + offset1 * math.cos(angle1)
        control1_y = start_y + offset1 * math.sin(angle1)
        
        # 第二個控制點（接近終點）
        offset2 = distance * randomness * random.uniform(0.2, 0.4)
        angle2 = math.atan2(end_y - start_y, end_x - start_x) + random.uniform(-0.5, 0.5)
        control2_x = end_x - offset2 * math.cos(angle2)
        control2_y = end_y - offset2 * math.sin(angle2)
        
        # 生成路徑
        path = []
        for i in range(steps + 1):
            t = i / steps
            # 三次貝茲曲線公式
            x = (
                (1 - t)**3 * start_x +
                3 * (1 - t)**2 * t * control1_x +
                3 * (1 - t) * t**2 * control2_x +
                t**3 * end_x
            )
            y = (
                (1 - t)**3 * start_y +
                3 * (1 - t)**2 * t * control1_y +
                3 * (1 - t) * t**2 * control2_y +
                t**3 * end_y
            )
            path.append((int(x), int(y)))
        return path
    
    def _follow_path(
        self,
        path: List[Tuple[int, int]],
        duration: float,
        easing: str
    ) -> None:
        """沿著路徑移動滑鼠（帶速度變化）
        
        Args:
            path: 路徑點列表
            duration: 總持續時間
            easing: 速度曲線
        """
        start_time = time.time()
        total_steps = len(path)
        
        for i, (x, y) in enumerate(path):
            # 計算當前進度（0.0 ~ 1.0）
            progress = i / (total_steps - 1) if total_steps > 1 else 1.0
            
            # 套用速度曲線
            eased_progress = self._apply_easing(progress, easing)
            
            # 計算延遲時間（確保總時間符合 duration）
            target_time = start_time + eased_progress * duration
            wait_time = target_time - time.time()
            if wait_time > 0:
                time.sleep(wait_time)
            
            # 移動滑鼠
            self.move_function(x, y)
    
    def _apply_easing(self, t: float, easing: str) -> float:
        """套用速度曲線（Easing Function）
        
        Args:
            t: 進度 (0.0 ~ 1.0)
            easing: 曲線類型
            
        Returns:
            調整後的進度 (0.0 ~ 1.0)
        """
        if easing == "linear":
            return t
        elif easing == "ease_in":
            # 慢速啟動（二次函數）
            return t * t
        elif easing == "ease_out":
            # 慢速結束
            return 1 - (1 - t) * (1 - t)
        elif easing == "ease_in_out":
            # 慢速啟動與結束（S曲線）
            if t < 0.5:
                return 2 * t * t
            else:
                return 1 - 2 * (1 - t) * (1 - t)
        else:
            return t


# ====== 使用範例 ======
if __name__ == "__main__":
    import tkinter as tk
    
    # 創建測試視窗
    root = tk.Tk()
    root.title("BezierMouse 測試")
    root.geometry("800x600")
    
    # 創建畫布
    canvas = tk.Canvas(root, bg="white")
    canvas.pack(fill="both", expand=True)
    
    # 創建移動器
    mover = BezierMouseMover()
    
    def on_click(event):
        """點擊畫布後移動滑鼠"""
        # 取得當前位置
        start_x, start_y = mover.get_current_position()
        
        # 畫起點
        canvas.create_oval(start_x-3, start_y-3, start_x+3, start_y+3, fill="green")
        
        # 畫終點
        canvas.create_oval(event.x-3, event.y-3, event.x+3, event.y+3, fill="red")
        
        # 移動滑鼠（使用三次貝茲曲線）
        print(f"移動: ({start_x}, {start_y}) -> ({event.x}, {event.y})")
        mover.move_to(
            event.x, event.y,
            duration=0.5,
            curve_type="cubic",
            randomness=0.3,
            easing="ease_in_out"
        )
    
    canvas.bind("<Button-1>", on_click)
    
    # 說明
    label = tk.Label(
        root, 
        text="點擊畫布任意位置，滑鼠將以貝茲曲線移動\n綠點 = 起點 | 紅點 = 終點",
        font=("Arial", 12)
    )
    label.pack(pady=10)
    
    root.mainloop()
