"""
ChroLens 區塊編輯器核心 - 新架構
參考 Blockly、Node-RED 和 Playwright Codegen 設計理念
支援雙向轉換：JSON 腳本 ↔ 視覺化區塊
"""

import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum


class ActionType(Enum):
    """動作類型枚舉"""
    # 滑鼠動作
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_DOUBLE_CLICK = "mouse_double_click"
    MOUSE_RIGHT_CLICK = "mouse_right_click"
    MOUSE_PRESS = "mouse_press"
    MOUSE_RELEASE = "mouse_release"
    MOUSE_DRAG = "mouse_drag"
    MOUSE_SCROLL = "mouse_scroll"
    
    # 鍵盤動作
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"
    KEY_TYPE = "key_type"
    KEY_HOTKEY = "key_hotkey"
    
    # 等待動作
    WAIT_TIME = "wait_time"
    WAIT_CLICK = "wait_click"
    
    # 控制流程
    LOOP_START = "loop_start"
    LOOP_END = "loop_end"
    IF_CONDITION = "if_condition"
    COMMENT = "comment"


class ParamType(Enum):
    """參數類型枚舉"""
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    CHOICE = "choice"


@dataclass
class ActionParam:
    """動作參數定義"""
    name: str  # 參數名稱
    param_type: ParamType  # 參數類型
    default: Any  # 預設值
    choices: Optional[List[str]] = None  # 選項（用於 choice 類型）
    min_value: Optional[float] = None  # 最小值
    max_value: Optional[float] = None  # 最大值
    description: str = ""  # 參數說明


@dataclass
class ActionDefinition:
    """動作定義（範本）"""
    action_type: ActionType  # 動作類型
    name: str  # 顯示名稱
    icon: str  # 圖示（emoji 或 unicode）
    category: str  # 分類（mouse, keyboard, wait, control）
    color: str  # 顏色（用於 UI 顯示）
    params: List[ActionParam] = field(default_factory=list)  # 參數列表
    description: str = ""  # 動作說明
    
    def create_instance(self, **param_values) -> 'ActionBlock':
        """創建動作實例"""
        return ActionBlock(
            action_type=self.action_type,
            definition=self,
            params=param_values
        )


@dataclass
class ActionBlock:
    """動作區塊實例（使用者創建的具體動作）"""
    action_type: ActionType  # 動作類型
    definition: ActionDefinition  # 動作定義
    params: Dict[str, Any] = field(default_factory=dict)  # 實際參數值
    timestamp: float = 0.0  # 時間戳（用於排序）
    enabled: bool = True  # 是否啟用
    block_id: str = ""  # 區塊唯一 ID
    
    def __post_init__(self):
        """初始化後處理"""
        if not self.block_id:
            self.block_id = f"{self.action_type.value}_{int(time.time() * 1000000)}"
        
        # 填充缺失的參數（使用預設值）
        for param_def in self.definition.params:
            if param_def.name not in self.params:
                self.params[param_def.name] = param_def.default
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典（用於序列化）"""
        return {
            "action_type": self.action_type.value,
            "params": self.params,
            "timestamp": self.timestamp,
            "enabled": self.enabled,
            "block_id": self.block_id
        }
    
    def validate(self) -> Tuple[bool, str]:
        """驗證參數有效性"""
        for param_def in self.definition.params:
            param_name = param_def.name
            if param_name not in self.params:
                return False, f"缺少參數: {param_name}"
            
            value = self.params[param_name]
            
            # 類型檢查
            if param_def.param_type == ParamType.INT:
                if not isinstance(value, int):
                    try:
                        self.params[param_name] = int(value)
                    except:
                        return False, f"參數 {param_name} 必須是整數"
            
            elif param_def.param_type == ParamType.FLOAT:
                if not isinstance(value, (int, float)):
                    try:
                        self.params[param_name] = float(value)
                    except:
                        return False, f"參數 {param_name} 必須是數字"
            
            elif param_def.param_type == ParamType.CHOICE:
                if param_def.choices and value not in param_def.choices:
                    return False, f"參數 {param_name} 必須是 {param_def.choices} 之一"
            
            # 範圍檢查
            if param_def.min_value is not None:
                if float(value) < param_def.min_value:
                    return False, f"參數 {param_name} 不能小於 {param_def.min_value}"
            
            if param_def.max_value is not None:
                if float(value) > param_def.max_value:
                    return False, f"參數 {param_name} 不能大於 {param_def.max_value}"
        
        return True, "OK"


class ActionLibrary:
    """動作庫 - 管理所有可用的動作定義"""
    
    def __init__(self):
        self.definitions: Dict[ActionType, ActionDefinition] = {}
        self._init_default_actions()
    
    def _init_default_actions(self):
        """初始化預設動作庫"""
        
        # === 滑鼠動作 ===
        self.register(ActionDefinition(
            action_type=ActionType.MOUSE_MOVE,
            name="移動滑鼠",
            icon="🖱️",
            category="mouse",
            color="#4A90E2",
            params=[
                ActionParam("x", ParamType.INT, 0, description="X 座標"),
                ActionParam("y", ParamType.INT, 0, description="Y 座標"),
                ActionParam("duration", ParamType.FLOAT, 0.0, min_value=0, description="移動時間（秒）")
            ],
            description="移動滑鼠到指定座標"
        ))
        
        self.register(ActionDefinition(
            action_type=ActionType.MOUSE_CLICK,
            name="左鍵點擊",
            icon="👆",
            category="mouse",
            color="#4A90E2",
            params=[
                ActionParam("button", ParamType.CHOICE, "left", 
                           choices=["left", "right", "middle"], description="按鍵")
            ],
            description="執行滑鼠點擊"
        ))
        
        self.register(ActionDefinition(
            action_type=ActionType.MOUSE_DOUBLE_CLICK,
            name="雙擊",
            icon="👆👆",
            category="mouse",
            color="#4A90E2",
            params=[],
            description="執行滑鼠雙擊"
        ))
        
        self.register(ActionDefinition(
            action_type=ActionType.MOUSE_RIGHT_CLICK,
            name="右鍵點擊",
            icon="👉",
            category="mouse",
            color="#4A90E2",
            params=[],
            description="執行滑鼠右鍵點擊"
        ))
        
        self.register(ActionDefinition(
            action_type=ActionType.MOUSE_DRAG,
            name="拖曳滑鼠",
            icon="✋",
            category="mouse",
            color="#4A90E2",
            params=[
                ActionParam("from_x", ParamType.INT, 0, description="起始 X"),
                ActionParam("from_y", ParamType.INT, 0, description="起始 Y"),
                ActionParam("to_x", ParamType.INT, 0, description="目標 X"),
                ActionParam("to_y", ParamType.INT, 0, description="目標 Y"),
                ActionParam("duration", ParamType.FLOAT, 0.5, min_value=0, description="拖曳時間")
            ],
            description="從一點拖曳到另一點"
        ))
        
        self.register(ActionDefinition(
            action_type=ActionType.MOUSE_SCROLL,
            name="滾動滑鼠",
            icon="🔄",
            category="mouse",
            color="#4A90E2",
            params=[
                ActionParam("amount", ParamType.INT, 1, description="滾動量（正數向上，負數向下）")
            ],
            description="滾動滑鼠滾輪"
        ))
        
        # === 鍵盤動作 ===
        self.register(ActionDefinition(
            action_type=ActionType.KEY_PRESS,
            name="按一下按鍵",
            icon="⌨️",
            category="keyboard",
            color="#50C878",
            params=[
                ActionParam("key", ParamType.STRING, "", description="按鍵名稱")
            ],
            description="按一下鍵盤按鍵（按下後立即放開）"
        ))
        
        self.register(ActionDefinition(
            action_type=ActionType.KEY_RELEASE,
            name="按住按鍵",
            icon="⌨️⏱️",
            category="keyboard",
            color="#50C878",
            params=[
                ActionParam("key", ParamType.STRING, "", description="按鍵名稱"),
                ActionParam("duration", ParamType.FLOAT, 1.0, min_value=0, description="按住時間（秒）")
            ],
            description="按住鍵盤按鍵一段時間"
        ))
        
        self.register(ActionDefinition(
            action_type=ActionType.KEY_TYPE,
            name="輸入文字",
            icon="✍️",
            category="keyboard",
            color="#50C878",
            params=[
                ActionParam("text", ParamType.STRING, "", description="要輸入的文字"),
                ActionParam("interval", ParamType.FLOAT, 0.01, min_value=0, description="字元間隔（秒）")
            ],
            description="輸入一段文字"
        ))
        
        self.register(ActionDefinition(
            action_type=ActionType.KEY_HOTKEY,
            name="快捷鍵組合",
            icon="🎹",
            category="keyboard",
            color="#50C878",
            params=[
                ActionParam("keys", ParamType.STRING, "", description="組合鍵（如 ctrl+c）")
            ],
            description="執行快捷鍵組合"
        ))
        
        # === 等待動作 ===
        self.register(ActionDefinition(
            action_type=ActionType.WAIT_TIME,
            name="等待時間",
            icon="⏱️",
            category="wait",
            color="#FFA500",
            params=[
                ActionParam("seconds", ParamType.FLOAT, 1.0, min_value=0, description="等待秒數")
            ],
            description="等待指定時間"
        ))
        
        # === 控制流程 ===
        self.register(ActionDefinition(
            action_type=ActionType.LOOP_START,
            name="重複開始",
            icon="🔁",
            category="control",
            color="#9B59B6",
            params=[
                ActionParam("count", ParamType.INT, 1, min_value=0, description="重複次數（0=無限）")
            ],
            description="開始重複執行（需搭配重複結束）"
        ))
        
        self.register(ActionDefinition(
            action_type=ActionType.LOOP_END,
            name="重複結束",
            icon="🔚",
            category="control",
            color="#9B59B6",
            params=[],
            description="結束重複區塊"
        ))
        
        self.register(ActionDefinition(
            action_type=ActionType.COMMENT,
            name="註解",
            icon="💬",
            category="control",
            color="#95A5A6",
            params=[
                ActionParam("text", ParamType.STRING, "", description="註解內容")
            ],
            description="添加註解說明"
        ))
    
    def register(self, definition: ActionDefinition):
        """註冊動作定義"""
        self.definitions[definition.action_type] = definition
    
    def get(self, action_type: ActionType) -> Optional[ActionDefinition]:
        """獲取動作定義"""
        return self.definitions.get(action_type)
    
    def get_by_category(self, category: str) -> List[ActionDefinition]:
        """按分類獲取動作定義"""
        return [d for d in self.definitions.values() if d.category == category]
    
    def get_all_categories(self) -> List[str]:
        """獲取所有分類"""
        return list(set(d.category for d in self.definitions.values()))


class ScriptSerializer:
    """腳本序列化器 - 負責 JSON ↔ ActionBlock 轉換"""
    
    def __init__(self, action_library: ActionLibrary):
        self.library = action_library
    
    def json_to_blocks(self, json_data: Dict[str, Any]) -> List[ActionBlock]:
        """
        將錄製的 JSON 腳本轉換為動作區塊列表
        
        Args:
            json_data: 錄製的 JSON 格式 {"events": [...], "settings": {...}}
        
        Returns:
            動作區塊列表
        """
        blocks = []
        events = json_data.get("events", [])
        
        # 預處理：配對鍵盤 down+up 事件
        processed_events = self._pair_keyboard_events(events)
        
        for event in processed_events:
            block = self._event_to_block(event)
            if block:
                blocks.append(block)
        
        # 按時間戳排序
        blocks.sort(key=lambda b: b.timestamp)
        
        return blocks
    
    def _pair_keyboard_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        配對鍵盤 down+up 事件，轉換為按一下按鍵
        
        邏輯：
        - 按下A -> 放開A = 按一下A
        - 按下A -> 按下B -> 放開A -> 放開B = 按一下A + 按一下B
        """
        processed = []
        pending_keys = {}  # {key_name: (index, down_event)}
        skip_indices = set()
        
        for i, event in enumerate(events):
            event_type = event.get("type", "")
            event_name = event.get("event", "")
            
            # 只處理鍵盤事件
            if event_type == "keyboard":
                key_name = event.get("name", "")
                
                if event_name == "down":
                    # 記錄按下事件
                    pending_keys[key_name] = (i, event)
                
                elif event_name == "up" and key_name in pending_keys:
                    # 找到配對的 up 事件
                    down_index, down_event = pending_keys[key_name]
                    
                    # 創建 "按一下" 事件（合併 down+up）
                    key_press_event = {
                        "type": "keyboard",
                        "event": "press",  # 新的事件類型：按一下
                        "name": key_name,
                        "time": down_event.get("time", 0.0)
                    }
                    
                    # 標記原始事件為已處理
                    skip_indices.add(down_index)
                    skip_indices.add(i)
                    
                    processed.append(key_press_event)
                    del pending_keys[key_name]
                    continue
        
        # 處理未配對的 down 事件（可能是長按）
        for key_name, (index, down_event) in pending_keys.items():
            if index not in skip_indices:
                # 沒有配對的 up，保留原始 down 事件
                processed.append(down_event)
                skip_indices.add(index)
        
        # 加入其他非鍵盤事件
        for i, event in enumerate(events):
            if i not in skip_indices:
                processed.append(event)
        
        # 按時間排序
        processed.sort(key=lambda e: e.get("time", 0.0))
        
        return processed
    
    def _event_to_block(self, event: Dict[str, Any]) -> Optional[ActionBlock]:
        """將單個事件轉換為動作區塊"""
        event_type = event.get("type", "")
        event_name = event.get("event", "")  # 新格式使用 "event" 欄位
        timestamp = event.get("time", 0.0)
        
        # ====== 處理新格式 (主程式錄製格式) ======
        # 新格式: {"type": "mouse", "event": "move", ...}
        if event_type == "mouse":
            # 滑鼠移動
            if event_name == "move":
                definition = self.library.get(ActionType.MOUSE_MOVE)
                if definition:
                    return definition.create_instance(
                        x=event.get("x", 0),
                        y=event.get("y", 0),
                        duration=0.0
                    )
            
            # 滑鼠按下 → 點擊
            elif event_name == "down":
                button = event.get("button", "left")
                definition = self.library.get(ActionType.MOUSE_CLICK)
                if definition:
                    return definition.create_instance(button=button)
            
            # 滑鼠滾輪
            elif event_name == "wheel":
                delta = event.get("delta", 0)
                definition = self.library.get(ActionType.MOUSE_SCROLL)
                if definition:
                    return definition.create_instance(delta=delta)
        
        # 鍵盤事件: {"type": "keyboard", "event": "press/down/up", "name": "a"}
        elif event_type == "keyboard":
            key_name = event.get("name", "")
            
            # "press" 表示已配對的按一下按鍵
            if event_name == "press":
                definition = self.library.get(ActionType.KEY_PRESS)
                if definition:
                    return definition.create_instance(key=key_name)
            
            # 未配對的 "down" 表示按住不放（保留原始行為）
            elif event_name == "down":
                definition = self.library.get(ActionType.KEY_RELEASE)  # 使用 "按住按鍵"
                if definition:
                    return definition.create_instance(key=key_name, duration=0.5)
            
            # 忽略單獨的 "up" 事件（已被配對處理）
            elif event_name == "up":
                pass  # 跳過
        
        # ====== 處理舊格式 (向後兼容) ======
        # 舊格式: {"type": "mouse_move", ...}
        
        # 滑鼠移動
        if event_type == "mouse_move":
            definition = self.library.get(ActionType.MOUSE_MOVE)
            if definition:
                return definition.create_instance(
                    x=event.get("x", 0),
                    y=event.get("y", 0),
                    duration=0.0
                )
        
        # 滑鼠按下/放開 → 合併為點擊
        elif event_type in ["mouse_down", "mouse_up"]:
            button = event.get("button", "left")
            # 這裡簡化處理，實際應該配對 down/up
            if event_type == "mouse_down":
                definition = self.library.get(ActionType.MOUSE_CLICK)
                if definition:
                    return definition.create_instance(button=button)
        
        # 鍵盤按下/放開
        elif event_type == "key_down":
            key = event.get("key", "")
            definition = self.library.get(ActionType.KEY_PRESS)
            if definition:
                return definition.create_instance(key=key)
        
        elif event_type == "key_up":
            key = event.get("key", "")
            definition = self.library.get(ActionType.KEY_RELEASE)
            if definition:
                return definition.create_instance(key=key)
        
        # 等待
        elif event_type == "wait":
            duration = event.get("duration", 1.0)
            definition = self.library.get(ActionType.WAIT_TIME)
            if definition:
                return definition.create_instance(seconds=duration)
        
        return None
    
    def blocks_to_json(self, blocks: List[ActionBlock]) -> Dict[str, Any]:
        """
        將動作區塊列表轉換為可執行的 JSON 腳本
        
        Args:
            blocks: 動作區塊列表
        
        Returns:
            JSON 格式的腳本
        """
        events = []
        cumulative_time = 0.0
        
        for block in blocks:
            if not block.enabled:
                continue
            
            result = self._block_to_event(block, cumulative_time)
            if result:
                # 處理返回列表的情況（如點擊會返回多個事件）
                if isinstance(result, list):
                    for event in result:
                        events.append(event)
                        if isinstance(event, dict):
                            cumulative_time = event.get("time", cumulative_time)
                else:
                    events.append(result)
                    if isinstance(result, dict):
                        cumulative_time = result.get("time", cumulative_time)
        
        return {
            "events": events,
            "settings": {
                "version": "2.6.5",
                "created_by": "visual_editor"
            }
        }
    
    def _block_to_event(self, block: ActionBlock, current_time: float) -> Optional[Dict[str, Any]]:
        """將動作區塊轉換為事件"""
        event = {"time": current_time}
        
        # 滑鼠移動
        if block.action_type == ActionType.MOUSE_MOVE:
            event.update({
                "type": "mouse_move",
                "x": block.params.get("x", 0),
                "y": block.params.get("y", 0)
            })
        
        # 滑鼠點擊
        elif block.action_type == ActionType.MOUSE_CLICK:
            button = block.params.get("button", "left")
            # 生成按下和放開兩個事件
            return [
                {"type": "mouse_down", "button": button, "time": current_time},
                {"type": "mouse_up", "button": button, "time": current_time + 0.05}
            ]
        
        # 按一下按鍵（生成 down+up）
        elif block.action_type == ActionType.KEY_PRESS:
            key = block.params.get("key", "")
            return [
                {"type": "keyboard", "event": "down", "name": key, "time": current_time},
                {"type": "keyboard", "event": "up", "name": key, "time": current_time + 0.05}
            ]
        
        # 按住按鍵（生成 down，延遲後 up）
        elif block.action_type == ActionType.KEY_RELEASE:
            key = block.params.get("key", "")
            duration = block.params.get("duration", 1.0)
            return [
                {"type": "keyboard", "event": "down", "name": key, "time": current_time},
                {"type": "keyboard", "event": "up", "name": key, "time": current_time + duration}
            ]
        
        # 輸入文字
        elif block.action_type == ActionType.KEY_TYPE:
            text = block.params.get("text", "")
            interval = block.params.get("interval", 0.01)
            events = []
            for i, char in enumerate(text):
                events.append({
                    "type": "key_down",
                    "key": char,
                    "time": current_time + i * interval
                })
                events.append({
                    "type": "key_up",
                    "key": char,
                    "time": current_time + i * interval + 0.01
                })
            return events
        
        # 等待
        elif block.action_type == ActionType.WAIT_TIME:
            seconds = block.params.get("seconds", 1.0)
            event.update({
                "type": "wait",
                "duration": seconds
            })
        
        else:
            return None
        
        return event


# 全域實例
ACTION_LIBRARY = ActionLibrary()
