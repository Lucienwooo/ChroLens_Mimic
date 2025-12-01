#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試文字指令解析
"""

import re
import time

def parse_time(time_str):
    """解析時間字串為秒數"""
    time_str = time_str.replace("T=", "").strip()
    
    total_seconds = 0.0
    
    # 解析分鐘
    if "m" in time_str:
        parts = time_str.split("m")
        total_seconds += float(parts[0]) * 60
        time_str = parts[1]
    
    # 解析秒和毫秒
    if "s" in time_str:
        parts = time_str.split("s")
        total_seconds += float(parts[0])
        if len(parts) > 1 and parts[1]:
            total_seconds += float(parts[1]) / 1000
    
    return total_seconds

# 測試案例
test_lines = [
    ">移動至(1612,1163), 延遲0ms, T=0s000",
    ">移動至(1610,1163), 延遲0ms, T=0s021",
    ">按Y, 延遲50ms, T=1s000",
    ">左鍵點擊(100,200), 延遲0ms, T=2s000",
]

print("=== 測試文字指令解析 (修復後) ===\n")

for line in test_lines:
    print(f"原始指令: {line}")
    
    if line.startswith(">"):
        # ✅ 智能分割（保護括號內的逗號）
        line_content = line[1:]
        
        # 先保護括號內的內容
        protected = re.sub(r'\(([^)]+)\)', lambda m: f"({m.group(1).replace(',', '§')})", line_content)
        parts_raw = protected.split(",")
        # 還原括號內的逗號
        parts = [p.replace('§', ',') for p in parts_raw]
        
        print(f"  分割結果: {parts}")
        print(f"  parts數量: {len(parts)}")
        
        if len(parts) >= 2:
            action = parts[0].strip()
            
            # 智能判斷
            if len(parts) == 2 and "T=" in parts[1]:
                delay_str = "0ms"
                time_str = parts[1].strip()
                print(f"  → 模式A (缺少延遲): 動作='{action}', 延遲='{delay_str}', 時間='{time_str}'")
            else:
                delay_str = parts[1].strip() if len(parts) > 1 else "0ms"
                time_str = parts[2].strip() if len(parts) > 2 else "T=0s000"
                print(f"  → 模式B (完整格式): 動作='{action}', 延遲='{delay_str}', 時間='{time_str}'")
            
            # 檢查座標
            coords = re.search(r'\((\d+),(\d+)\)', action)
            if coords:
                x, y = int(coords.group(1)), int(coords.group(2))
                print(f"  ✓ 滑鼠操作: 座標=({x},{y})")
                
                if "移動至" in action:
                    print(f"  ✓ 類型: mouse move")
                elif "點擊" in action or "鍵" in action:
                    button = "right" if "右鍵" in action else "left"
                    print(f"  ✓ 類型: mouse click ({button})")
            else:
                print(f"  ✓ 鍵盤操作")
    
    print()

print("\n=== 測試完成 ===")
