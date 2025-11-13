"""
ChroLens Script Parser - 腳本解析器
支援簡化的 Python-like 語法，並支援中文/日文指令

語法範例：
    move_to(100, 200) 或 移動(100, 200) 或 移動する(100, 200)
    click() 或 點擊() 或 クリック()
    delay(1000) 或 延遲(1000) 或 待機(1000)
    type_text("Hello") 或 輸入文字("Hello") 或 文字入力("Hello")
    press_key("Enter") 或 按鍵("Enter") 或 キー押下("Enter")
"""

import re
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


# 多語言指令映射表
COMMAND_MAP = {
    # 中文指令
    "移動": "move_to",
    "移動到": "move_to",
    "點擊": "click",
    "單擊": "click",
    "雙擊": "double_click",
    "右鍵": "right_click",
    "右鍵點擊": "right_click",
    "輸入文字": "type_text",
    "輸入": "type_text",
    "打字": "type_text",
    "按鍵": "press_key",
    "按下": "press_key",
    "延遲": "delay",
    "等待": "delay",
    "暫停": "delay",
    "日誌": "log",
    "記錄": "log",
    "輸出": "log",
    
    # 日文指令
    "移動する": "move_to",
    "移動": "move_to",
    "クリック": "click",
    "ダブルクリック": "double_click",
    "右クリック": "right_click",
    "文字入力": "type_text",
    "入力": "type_text",
    "キー押下": "press_key",
    "待機": "delay",
    "ログ": "log",
}


@dataclass
class Instruction:
    """指令數據類"""
    command: str
    args: List[Any]
    kwargs: Dict[str, Any]
    line_number: int
    raw_line: str


class ScriptParser:
    """腳本解析器"""
    
    def __init__(self):
        self.instructions = []
        self.variables = {}
        self.errors = []
    
    def parse(self, script_text: str) -> tuple[List[Instruction], List[str]]:
        """
        解析腳本文字
        
        Returns:
            (instructions, errors)
        """
        self.instructions = []
        self.errors = []
        self.variables = {}
        
        lines = script_text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            original_line = line
            line = line.strip()
            
            # 跳過空行和註解
            if not line or line.startswith('#'):
                continue
            
            try:
                inst = self._parse_line(line, line_num, original_line)
                if inst:
                    self.instructions.append(inst)
            except Exception as e:
                self.errors.append(f"Line {line_num}: {e}")
        
        return self.instructions, self.errors
    
    def _parse_line(self, line: str, line_num: int, raw_line: str) -> Optional[Instruction]:
        """解析單行指令（支援中文/日文指令）"""
        
        # 函式調用: command(args, kwargs)
        # 支援中文/日文/英文指令名稱
        match = re.match(r'([\w\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+)\((.*?)\)\s*$', line)
        if match:
            command = match.group(1)
            args_str = match.group(2)
            
            # 檢查是否為多語言指令，轉換為英文指令
            if command in COMMAND_MAP:
                command = COMMAND_MAP[command]
            
            args, kwargs = self._parse_arguments(args_str)
            
            return Instruction(
                command=command,
                args=args,
                kwargs=kwargs,
                line_number=line_num,
                raw_line=raw_line
            )
        
        # 變數賦值: variable = value
        match = re.match(r'(\w+)\s*=\s*(.+)', line)
        if match:
            var_name = match.group(1)
            value = self._eval_expression(match.group(2))
            self.variables[var_name] = value
            
            return Instruction(
                command='assign',
                args=[var_name, value],
                kwargs={},
                line_number=line_num,
                raw_line=raw_line
            )
        
        raise SyntaxError(f"無法解析的語法: {line}")
    
    def _parse_arguments(self, args_str: str) -> tuple[List[Any], Dict[str, Any]]:
        """解析參數"""
        args = []
        kwargs = {}
        
        if not args_str.strip():
            return args, kwargs
        
        # 簡單的參數分割（不處理巢狀括號）
        parts = []
        current = ""
        in_string = False
        string_char = None
        
        for char in args_str:
            if char in ('"', "'") and (not in_string or char == string_char):
                in_string = not in_string
                string_char = char if in_string else None
            
            if char == ',' and not in_string:
                parts.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            parts.append(current.strip())
        
        for part in parts:
            if '=' in part and not part.startswith('"') and not part.startswith("'"):
                # 關鍵字參數
                key, value = part.split('=', 1)
                kwargs[key.strip()] = self._eval_expression(value.strip())
            else:
                # 位置參數
                args.append(self._eval_expression(part))
        
        return args, kwargs
    
    def _eval_expression(self, expr: str) -> Any:
        """評估表達式"""
        expr = expr.strip()
        
        # 字串
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]
        
        # 數字
        try:
            if '.' in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass
        
        # 布林值
        if expr.lower() == 'true':
            return True
        if expr.lower() == 'false':
            return False
        
        # 變數
        if expr in self.variables:
            return self.variables[expr]
        
        # 未知，返回原字串
        return expr


class ScriptExecutor:
    """腳本執行器"""
    
    def __init__(self, logger=None):
        """
        初始化執行器
        
        Args:
            logger: 日誌函式（可選）
        """
        self.parser = ScriptParser()
        self.logger = logger or print
        self.variables = {}
        self.stop_flag = False
    
    def execute(self, script_text: str) -> bool:
        """
        執行腳本
        
        Returns:
            是否成功執行
        """
        instructions, errors = self.parser.parse(script_text)
        
        if errors:
            for error in errors:
                self.logger(f"[錯誤] {error}")
            return False
        
        self.stop_flag = False
        
        for inst in instructions:
            if self.stop_flag:
                self.logger("[資訊] 腳本已停止")
                break
            
            try:
                self._execute_instruction(inst)
            except Exception as e:
                self.logger(f"[錯誤] Line {inst.line_number}: {e}")
                return False
        
        self.logger("[資訊] 腳本執行完成")
        return True
    
    def stop(self):
        """停止執行"""
        self.stop_flag = True
    
    def _execute_instruction(self, inst: Instruction):
        """執行單一指令"""
        # 指令映射
        command_map = {
            'move_to': self._cmd_move_to,
            'click': self._cmd_click,
            'double_click': self._cmd_double_click,
            'right_click': self._cmd_right_click,
            'type_text': self._cmd_type_text,
            'press_key': self._cmd_press_key,
            'delay': self._cmd_delay,
            'log': self._cmd_log,
            'assign': self._cmd_assign,
        }
        
        cmd_func = command_map.get(inst.command)
        if cmd_func:
            self.logger(f"[執行] Line {inst.line_number}: {inst.raw_line.strip()}")
            cmd_func(*inst.args, **inst.kwargs)
        else:
            raise ValueError(f"未知的指令: {inst.command}")
    
    # ===== 指令實作 =====
    
    def _cmd_move_to(self, x: int, y: int):
        """移動滑鼠到指定座標"""
        try:
            import mouse
            mouse.move(x, y)
        except ImportError:
            self.logger("[警告] 需要安裝 mouse 套件")
    
    def _cmd_click(self, button: str = 'left'):
        """點擊滑鼠"""
        try:
            import mouse
            mouse.click(button)
        except ImportError:
            self.logger("[警告] 需要安裝 mouse 套件")
    
    def _cmd_double_click(self):
        """雙擊滑鼠"""
        try:
            import mouse
            mouse.double_click()
        except ImportError:
            self.logger("[警告] 需要安裝 mouse 套件")
    
    def _cmd_right_click(self):
        """右鍵點擊"""
        try:
            import mouse
            mouse.right_click()
        except ImportError:
            self.logger("[警告] 需要安裝 mouse 套件")
    
    def _cmd_type_text(self, text: str):
        """輸入文字"""
        try:
            import keyboard
            keyboard.write(text)
        except ImportError:
            self.logger("[警告] 需要安裝 keyboard 套件")
    
    def _cmd_press_key(self, key: str):
        """按鍵"""
        try:
            import keyboard
            keyboard.press_and_release(key)
        except ImportError:
            self.logger("[警告] 需要安裝 keyboard 套件")
    
    def _cmd_delay(self, ms: int):
        """延遲（毫秒）"""
        time.sleep(ms / 1000)
    
    def _cmd_log(self, message: str):
        """輸出日誌"""
        self.logger(f"[腳本] {message}")
    
    def _cmd_assign(self, var_name: str, value: Any):
        """變數賦值"""
        self.variables[var_name] = value
        self.logger(f"[變數] {var_name} = {value}")


# ===== 測試範例 =====

if __name__ == "__main__":
    # 測試腳本
    test_script = """
# 自動登入範例腳本
move_to(500, 300)
click()
delay(500)
type_text("username")
press_key("tab")
type_text("password")
press_key("enter")
delay(2000)
log("登入完成")
"""
    
    print("=== ChroLens Script Parser 測試 ===\n")
    print("腳本內容：")
    print(test_script)
    print("\n執行結果：")
    print("=" * 50)
    
    executor = ScriptExecutor()
    executor.execute(test_script)
    
    print("=" * 50)
    print("\n測試完成！")
