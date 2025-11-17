# -*- coding: utf-8 -*-
"""
ChroLens 圖片指令解析器
解析和執行圖片識別相關的文字指令
"""

import re
import time
from typing import Dict, Any, Optional, Tuple, List
from image_recognition import ImageRecognition
import os


class ImageCommandParser:
    """圖片指令解析和執行器"""
    
    def __init__(self, image_dir: str = None):
        """
        初始化
        :param image_dir: 圖片模板目錄
        """
        self.image_dir = image_dir or os.path.join(os.path.dirname(__file__), "images", "templates")
        self.ir = ImageRecognition(confidence=0.75)
        self.labels = {}  # 標籤字典 {標籤名: 行號}
        self.current_line = 0
        
    def parse_labels(self, lines: List[str]) -> Dict[str, int]:
        """
        預先掃描所有標籤
        :param lines: 文字指令行列表
        :return: {標籤名: 行號}
        """
        labels = {}
        for i, line in enumerate(lines):
            line = line.strip()
            # 匹配標籤: #標籤名
            if line.startswith('#') and not line.startswith('#標籤'):
                label_name = line[1:].strip()
                labels[label_name] = i
        return labels
    
    def parse_image_command(self, command: str) -> Optional[Dict[str, Any]]:
        """
        解析圖片指令
        :param command: 文字指令
        :return: 解析後的指令字典
        """
        command = command.strip()
        
        # 模式1: >等待圖片[filename.png], 超時30s
        wait_pattern = r'>等待圖片\[([^\]]+)\],?\s*超時(\d+(?:\.\d+)?)[sS]?'
        match = re.match(wait_pattern, command)
        if match:
            return {
                'type': 'wait_image',
                'image': match.group(1),
                'timeout': float(match.group(2)),
                'has_branch': False
            }
        
        # 模式2: >點擊圖片[filename.png], 信心度0.8
        click_pattern = r'>點擊圖片\[([^\]]+)\](?:,?\s*信心度([\d.]+))?'
        match = re.match(click_pattern, command)
        if match:
            confidence = float(match.group(2)) if match.group(2) else 0.75
            return {
                'type': 'click_image',
                'image': match.group(1),
                'confidence': confidence,
                'has_branch': False
            }
        
        # 模式3: >如果存在[filename.png]
        exists_pattern = r'>如果存在\[([^\]]+)\]'
        match = re.match(exists_pattern, command)
        if match:
            return {
                'type': 'if_exists',
                'image': match.group(1),
                'has_branch': True
            }
        
        # 模式4: 分支指令
        branch_patterns = {
            '成功': r'\s*成功→(.+)',
            '失敗': r'\s*失敗→(.+)',
            '執行': r'\s*執行→(.+)'
        }
        
        for branch_type, pattern in branch_patterns.items():
            match = re.match(pattern, command)
            if match:
                action = match.group(1).strip()
                return {
                    'type': 'branch',
                    'branch_type': branch_type,
                    'action': action
                }
        
        return None
    
    def parse_branch_action(self, action: str) -> Dict[str, Any]:
        """
        解析分支動作
        :param action: 動作字串 (例: "跳到 #標籤A", "重試3次, 間隔1s", "繼續")
        :return: 動作字典
        """
        # 跳到標籤
        jump_pattern = r'跳到\s*#(.+)'
        match = re.match(jump_pattern, action)
        if match:
            return {
                'action_type': 'jump',
                'label': match.group(1).strip()
            }
        
        # 重試
        retry_pattern = r'重試(\d+)次(?:,?\s*間隔([\d.]+)[sS])?'
        match = re.match(retry_pattern, action)
        if match:
            return {
                'action_type': 'retry',
                'count': int(match.group(1)),
                'interval': float(match.group(2)) if match.group(2) else 1.0
            }
        
        # 繼續
        if action == '繼續':
            return {'action_type': 'continue'}
        
        return {'action_type': 'unknown', 'raw': action}
    
    def execute_image_command(self, cmd_dict: Dict[str, Any], 
                              next_lines: List[str] = None) -> Tuple[bool, Optional[str]]:
        """
        執行圖片指令
        :param cmd_dict: 指令字典
        :param next_lines: 後續行(用於讀取分支)
        :return: (成功/失敗, 跳轉標籤名或None)
        """
        cmd_type = cmd_dict.get('type')
        image_file = cmd_dict.get('image')
        
        if not image_file:
            return False, None
        
        # 構建完整路徑
        image_path = os.path.join(self.image_dir, image_file)
        
        try:
            # 等待圖片出現
            if cmd_type == 'wait_image':
                timeout = cmd_dict.get('timeout', 30.0)
                print(f"⏳ 等待圖片出現: {image_file} (超時 {timeout}s)")
                
                location = self.ir.wait_for_image(image_path, timeout=timeout)
                success = location is not None
                
                if success:
                    print(f"✓ 圖片已出現: {location}")
                else:
                    print(f"✗ 圖片等待超時")
                
                # 處理分支
                if next_lines and cmd_dict.get('has_branch'):
                    return self._handle_branch(success, next_lines)
                
                return success, None
            
            # 點擊圖片
            elif cmd_type == 'click_image':
                confidence = cmd_dict.get('confidence', 0.75)
                print(f"🖱️ 點擊圖片: {image_file} (信心度 {confidence})")
                
                # 更新識別器信心度
                self.ir.confidence = confidence
                success = self.ir.click_image(image_path)
                
                if success:
                    print(f"✓ 圖片點擊成功")
                else:
                    print(f"✗ 圖片點擊失敗 (未找到)")
                
                # 處理分支
                if next_lines and cmd_dict.get('has_branch'):
                    return self._handle_branch(success, next_lines)
                
                return success, None
            
            # 條件判斷
            elif cmd_type == 'if_exists':
                print(f"🔍 檢查圖片是否存在: {image_file}")
                
                exists = self.ir.image_exists(image_path)
                
                if exists:
                    print(f"✓ 圖片存在")
                else:
                    print(f"✗ 圖片不存在")
                
                # 處理分支
                if next_lines and cmd_dict.get('has_branch'):
                    return self._handle_branch(exists, next_lines)
                
                return exists, None
                
        except Exception as e:
            print(f"❌ 執行圖片指令時發生錯誤: {e}")
            return False, None
        
        return False, None
    
    def _handle_branch(self, success: bool, next_lines: List[str]) -> Tuple[bool, Optional[str]]:
        """
        處理分支邏輯
        :param success: 上一步是否成功
        :param next_lines: 後續行
        :return: (是否繼續執行, 跳轉標籤)
        """
        # 尋找對應的分支
        branch_key = '成功' if success else '失敗'
        if not success and branch_key == '失敗':
            # 對於 if_exists, 失敗分支是不存在的情況
            branch_key = '失敗'
        
        for line in next_lines[:5]:  # 只看接下來5行
            line = line.strip()
            if not line or line.startswith('>') or line.startswith('#'):
                break  # 遇到新指令或標籤就停止
            
            # 解析分支
            cmd = self.parse_image_command(line)
            if cmd and cmd.get('type') == 'branch':
                if cmd.get('branch_type') == branch_key or cmd.get('branch_type') == '執行':
                    action = self.parse_branch_action(cmd.get('action', ''))
                    
                    # 跳轉
                    if action.get('action_type') == 'jump':
                        label = action.get('label')
                        print(f"↪️ 跳轉到標籤: #{label}")
                        return True, label
                    
                    # 重試
                    elif action.get('action_type') == 'retry':
                        count = action.get('count', 3)
                        interval = action.get('interval', 1.0)
                        print(f"🔁 重試 {count} 次, 間隔 {interval}s")
                        # TODO: 實作重試邏輯
                        return False, None
                    
                    # 繼續
                    elif action.get('action_type') == 'continue':
                        print(f"➡️ 繼續執行")
                        return True, None
        
        return True, None


# 輔助函數
def is_image_command(line: str) -> bool:
    """
    判斷是否為圖片指令
    :param line: 文字指令行
    :return: True/False
    """
    line = line.strip()
    keywords = ['>等待圖片', '>點擊圖片', '>如果存在']
    return any(line.startswith(kw) for kw in keywords)


# 測試
if __name__ == "__main__":
    parser = ImageCommandParser()
    
    test_commands = [
        ">等待圖片[按鈕.png], 超時30s",
        ">點擊圖片[圖示.png], 信心度0.8",
        ">如果存在[錯誤.png]",
        "  成功→跳到 #錯誤處理",
        "  失敗→繼續",
    ]
    
    print("測試圖片指令解析:")
    print("=" * 50)
    for cmd in test_commands:
        result = parser.parse_image_command(cmd)
        print(f"指令: {cmd}")
        print(f"解析: {result}")
        print("-" * 50)
