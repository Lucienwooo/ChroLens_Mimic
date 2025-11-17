# -*- coding: utf-8 -*-
"""
ChroLens 文字指令 - 自動戰鬥擴充
將自動戰鬥功能整合到文字指令系統
"""

import re
from typing import Dict, List, Any, Optional
from auto_combat_system import AutoCombatSystem


class CombatCommandParser:
    """戰鬥指令解析器"""
    
    def __init__(self):
        self.combat_system = None
        self.current_config = {}
    
    def parse_combat_command(self, command: str) -> Optional[Dict[str, Any]]:
        """
        解析戰鬥指令
        
        支援的指令格式:
        >啟動自動戰鬥, 敵人[enemy.png], 攻擊鍵1, 技能[Q,W,E]
        >尋找並攻擊[enemy.png], 移動時間0.3s, 攻擊後延遲0.5s
        >如果發現[low_hp.png], 執行→跳到 #補血
        >循環攻擊[enemy.png], 直到消失, 最多10次
        >智能戰鬥, 優先級[boss.png>elite.png>normal.png]
        """
        command = command.strip()
        
        # 1. 啟動自動戰鬥
        pattern = r'>啟動自動戰鬥(?:,\s*敵人\[([^\]]+)\])?(?:,\s*攻擊鍵(\w+))?(?:,\s*技能\[([^\]]+)\])?'
        match = re.match(pattern, command)
        if match:
            enemies = match.group(1).split(',') if match.group(1) else []
            attack_key = match.group(2) or "1"
            skills = match.group(3).split(',') if match.group(3) else []
            
            return {
                'type': 'start_combat',
                'enemies': [e.strip() for e in enemies],
                'attack_key': attack_key,
                'skills': [s.strip() for s in skills]
            }
        
        # 2. 尋找並攻擊
        pattern = r'>尋找並攻擊\[([^\]]+)\](?:,\s*移動時間([\d.]+)s)?(?:,\s*攻擊後延遲([\d.]+)s)?'
        match = re.match(pattern, command)
        if match:
            return {
                'type': 'find_and_attack',
                'target': match.group(1),
                'move_duration': float(match.group(2)) if match.group(2) else 0.3,
                'attack_delay': float(match.group(3)) if match.group(3) else 0.5
            }
        
        # 3. 循環攻擊
        pattern = r'>循環攻擊\[([^\]]+)\](?:,\s*直到消失)?(?:,\s*最多(\d+)次)?'
        match = re.match(pattern, command)
        if match:
            return {
                'type': 'loop_attack',
                'target': match.group(1),
                'max_iterations': int(match.group(2)) if match.group(2) else 999
            }
        
        # 4. 智能戰鬥 (優先級)
        pattern = r'>智能戰鬥(?:,\s*優先級\[([^\]]+)\])?'
        match = re.match(pattern, command)
        if match:
            priority_str = match.group(1) or ""
            priorities = [p.strip() for p in priority_str.split('>')]
            
            return {
                'type': 'smart_combat',
                'priorities': priorities
            }
        
        # 5. 設定戰鬥區域
        pattern = r'>設定戰鬥區域\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)'
        match = re.match(pattern, command)
        if match:
            return {
                'type': 'set_region',
                'region': (int(match.group(1)), int(match.group(2)), 
                          int(match.group(3)), int(match.group(4)))
            }
        
        # 6. 停止戰鬥
        if command == '>停止自動戰鬥':
            return {'type': 'stop_combat'}
        
        # 7. 暫停/恢復
        if command == '>暫停戰鬥':
            return {'type': 'pause_combat'}
        if command == '>恢復戰鬥':
            return {'type': 'resume_combat'}
        
        return None
    
    def convert_to_json(self, command: str, time_offset: float = 0) -> Optional[Dict]:
        """
        將戰鬥指令轉換為JSON事件格式
        """
        cmd = self.parse_combat_command(command)
        if not cmd:
            return None
        
        event = {
            "type": "combat_action",
            "time": time_offset,
            "action": cmd['type'],
            "params": cmd
        }
        
        return event


# 文字指令範例
COMBAT_SCRIPT_EXAMPLES = """
# ChroLens 自動戰鬥腳本範例
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ============================================
# 範例1: 基礎自動打怪
# ============================================

#開始
>設定戰鬥區域(100, 100, 1000, 800)
>啟動自動戰鬥, 敵人[goblin.png, slime.png], 攻擊鍵1, 技能[Q,W,E]

# 等待10秒
>延遲10000ms

>停止自動戰鬥

# ============================================
# 範例2: 單一目標循環攻擊
# ============================================

#尋找怪物
>尋找並攻擊[boss.png], 移動時間0.5s, 攻擊後延遲0.3s
  成功→跳到 #攻擊序列
  失敗→跳到 #結束

#攻擊序列
>按Q, 延遲50ms, T=1s000
>延遲500ms
>按W, 延遲50ms, T=2s000
>延遲500ms
>按1, 延遲50ms, T=3s000
>延遲1000ms

# 檢查怪物是否還在
>如果存在[boss.png]
  執行→跳到 #攻擊序列

>跳到 #結束

# ============================================
# 範例3: 智能優先級戰鬥
# ============================================

#智能循環
>智能戰鬥, 優先級[boss.png>elite.png>normal.png]
  成功→跳到 #攻擊目標
  失敗→跳到 #巡邏

#攻擊目標
>按Space, 延遲100ms
>延遲500ms

# 檢查血量
>如果存在[low_hp.png]
  執行→跳到 #補血

>跳到 #智能循環

#補血
>按H, 延遲50ms
>延遲2000ms
>跳到 #智能循環

#巡邏
>按W, 延遲100ms
>延遲1000ms
>跳到 #智能循環

# ============================================
# 範例4: 完整自動練級腳本
# ============================================

#初始化
>設定戰鬥區域(200, 200, 1200, 800)
>啟動自動戰鬥, 敵人[mob1.png, mob2.png, mob3.png], 攻擊鍵1, 技能[Q,W,E,R]

#主循環
# 戰鬥系統會自動運作
>延遲5000ms

# 檢查特殊狀態
>如果存在[level_up.png]
  執行→跳到 #升級處理

>如果存在[inventory_full.png]
  執行→跳到 #整理背包

>如果存在[game_over.png]
  執行→跳到 #重生

# 繼續循環
>跳到 #主循環

#升級處理
>點擊圖片[level_up_ok.png]
>延遲1000ms
>跳到 #主循環

#整理背包
>暫停戰鬥
>按I, 延遲50ms
>延遲1000ms
# ... (整理背包操作)
>按I, 延遲50ms
>恢復戰鬥
>跳到 #主循環

#重生
>停止自動戰鬥
>點擊圖片[respawn_button.png]
>延遲5000ms
>跳到 #初始化

# ============================================
# 範例5: Boss戰專用腳本
# ============================================

#Boss戰開始
>等待圖片[boss_appear.png], 超時60s
  成功→繼續
  失敗→跳到 #結束

#Boss循環
>尋找並攻擊[boss_weak_point.png], 移動時間0.2s
  成功→跳到 #爆發輸出
  失敗→跳到 #普通攻擊

#爆發輸出
>按Q, 延遲50ms
>延遲300ms
>按W, 延遲50ms
>延遲300ms
>按E, 延遲50ms
>延遲300ms
>按R, 延遲50ms
>延遲1000ms
>跳到 #檢查狀態

#普通攻擊
>循環攻擊[boss.png], 最多3次
>跳到 #檢查狀態

#檢查狀態
# 血量檢查
>如果存在[hp_critical.png]
  執行→跳到 #緊急撤退

>如果存在[hp_low.png]
  執行→跳到 #喝藥

# Boss技能閃避
>如果存在[boss_skill_warning.png]
  執行→跳到 #閃避

# Boss是否死亡
>如果存在[boss_defeated.png]
  執行→跳到 #勝利

>跳到 #Boss循環

#喝藥
>按H, 延遲50ms
>延遲500ms
>跳到 #Boss循環

#閃避
>按Space, 延遲50ms
>按W, 延遲200ms
>延遲1000ms
>跳到 #Boss循環

#緊急撤退
>停止自動戰鬥
>按Shift, 延遲0ms
>按Space, 延遲100ms
>放開Space, 延遲0ms
>放開Shift, 延遲0ms
>延遲3000ms
>跳到 #結束

#勝利
>停止自動戰鬥
>點擊圖片[loot_all.png]
>延遲2000ms

#結束

# ============================================
# 指令說明
# ============================================
# 
# 1. 啟動自動戰鬥:
#    >啟動自動戰鬥, 敵人[圖1.png, 圖2.png], 攻擊鍵1, 技能[Q,W,E]
#    - 會自動循環尋找並攻擊敵人
#    - 自動使用技能 (如果圖示檢測到準備完成)
#    - 背景執行,不阻塞其他指令
# 
# 2. 尋找並攻擊:
#    >尋找並攻擊[怪物.png], 移動時間0.3s, 攻擊後延遲0.5s
#    - 單次尋找和攻擊
#    - 可配合分支做精確控制
# 
# 3. 循環攻擊:
#    >循環攻擊[目標.png], 直到消失, 最多10次
#    - 持續攻擊直到目標消失或達到次數上限
# 
# 4. 智能戰鬥:
#    >智能戰鬥, 優先級[Boss>精英>普通]
#    - 按優先級自動選擇目標
#    - 高優先級目標優先攻擊
# 
# 5. 設定區域:
#    >設定戰鬥區域(100, 100, 1000, 800)
#    - 限制搜尋範圍,提升效率
#    - (左, 上, 寬, 高)
# 
# 6. 控制指令:
#    >暫停戰鬥  - 暫停自動戰鬥系統
#    >恢復戰鬥  - 恢復自動戰鬥
#    >停止自動戰鬥 - 完全停止
# 
# ============================================
"""


def save_example_script():
    """儲存範例腳本"""
    import os
    filepath = os.path.join(os.path.dirname(__file__), "範例_自動戰鬥腳本.txt")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(COMBAT_SCRIPT_EXAMPLES)
    print(f"✓ 範例腳本已儲存: {filepath}")


if __name__ == "__main__":
    # 儲存範例
    save_example_script()
    
    # 測試解析
    parser = CombatCommandParser()
    
    test_commands = [
        ">啟動自動戰鬥, 敵人[goblin.png, slime.png], 攻擊鍵1, 技能[Q,W,E]",
        ">尋找並攻擊[boss.png], 移動時間0.5s, 攻擊後延遲0.3s",
        ">循環攻擊[enemy.png], 直到消失, 最多10次",
        ">智能戰鬥, 優先級[boss.png>elite.png>normal.png]",
        ">設定戰鬥區域(100, 100, 1000, 800)",
        ">停止自動戰鬥",
    ]
    
    print("\n測試指令解析:")
    print("=" * 60)
    for cmd in test_commands:
        result = parser.parse_combat_command(cmd)
        print(f"\n指令: {cmd}")
        print(f"解析: {result}")
