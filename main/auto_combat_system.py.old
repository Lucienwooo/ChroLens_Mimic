# -*- coding: utf-8 -*-
"""
ChroLens 自動戰鬥系統
支援圖片識別、智能決策、循環攻擊
"""

import time
import threading
from typing import List, Dict, Optional, Tuple, Callable
from image_recognition import ImageRecognition
import pyautogui
import os


class AutoCombatSystem:
    """自動戰鬥系統"""
    
    def __init__(self, templates_dir: str = None):
        """
        初始化
        :param templates_dir: 圖片模板目錄
        """
        self.templates_dir = templates_dir or os.path.join(os.path.dirname(__file__), "images", "templates")
        self.ir = ImageRecognition(confidence=0.75)
        
        # 戰鬥狀態
        self.is_running = False
        self.is_paused = False
        self.combat_thread = None
        
        # 統計數據
        self.stats = {
            "enemies_found": 0,
            "attacks_made": 0,
            "skills_used": 0,
            "items_looted": 0,
            "errors": 0,
            "start_time": None,
            "runtime": 0
        }
        
        # 戰鬥配置
        self.config = {
            "search_region": None,  # 搜尋區域 (left, top, width, height)
            "attack_key": "1",      # 攻擊按鍵
            "skill_keys": ["q", "w", "e"],  # 技能按鍵
            "hp_check_enabled": True,       # 是否檢查血量
            "loot_enabled": True,           # 是否拾取物品
            "move_duration": 0.3,           # 滑鼠移動時間
            "attack_delay": 0.5,            # 攻擊間隔
            "scan_interval": 1.0,           # 掃描間隔
        }
        
        # 圖片模板配置
        self.templates = {
            "enemy": [],        # 敵人圖片列表
            "low_hp": None,     # 血量低警告
            "skill_ready": [],  # 技能準備完成
            "loot": [],         # 可拾取物品
            "dead": None,       # 角色死亡
        }
        
        # 回調函數
        self.callbacks = {
            "on_enemy_found": None,
            "on_attack": None,
            "on_skill_used": None,
            "on_loot": None,
            "on_hp_low": None,
            "on_error": None,
        }
    
    def set_config(self, **kwargs):
        """設定配置"""
        self.config.update(kwargs)
    
    def set_templates(self, **kwargs):
        """設定圖片模板"""
        for key, value in kwargs.items():
            if key in self.templates:
                # 自動添加完整路徑
                if isinstance(value, list):
                    self.templates[key] = [self._get_template_path(v) for v in value]
                elif value:
                    self.templates[key] = self._get_template_path(value)
    
    def _get_template_path(self, filename: str) -> str:
        """取得模板完整路徑"""
        if os.path.isabs(filename):
            return filename
        return os.path.join(self.templates_dir, filename)
    
    def set_callback(self, event: str, callback: Callable):
        """設定回調函數"""
        if event in self.callbacks:
            self.callbacks[event] = callback
    
    def start(self):
        """啟動自動戰鬥"""
        if self.is_running:
            print("⚠️ 戰鬥系統已在運行中")
            return
        
        self.is_running = True
        self.is_paused = False
        self.stats["start_time"] = time.time()
        
        self.combat_thread = threading.Thread(target=self._combat_loop, daemon=True)
        self.combat_thread.start()
        
        print("✅ 自動戰鬥系統已啟動")
    
    def stop(self):
        """停止自動戰鬥"""
        self.is_running = False
        if self.combat_thread:
            self.combat_thread.join(timeout=2.0)
        
        self.stats["runtime"] = time.time() - self.stats["start_time"]
        print("⏹️ 自動戰鬥系統已停止")
        self._print_stats()
    
    def pause(self):
        """暫停戰鬥"""
        self.is_paused = True
        print("⏸️ 戰鬥已暫停")
    
    def resume(self):
        """恢復戰鬥"""
        self.is_paused = False
        print("▶️ 戰鬥已恢復")
    
    def _combat_loop(self):
        """戰鬥主循環"""
        print("🎮 進入戰鬥循環...")
        
        while self.is_running:
            try:
                # 暫停檢查
                if self.is_paused:
                    time.sleep(0.5)
                    continue
                
                # 1. 檢查是否死亡
                if self._check_death():
                    print("💀 角色已死亡,停止戰鬥")
                    self.stop()
                    break
                
                # 2. 檢查血量
                if self.config["hp_check_enabled"]:
                    if self._check_low_hp():
                        self._handle_low_hp()
                        continue
                
                # 3. 尋找並攻擊敵人
                enemy_found = self._find_and_attack_enemy()
                
                # 4. 如果沒有敵人,檢查物品
                if not enemy_found and self.config["loot_enabled"]:
                    self._loot_items()
                
                # 5. 等待下次掃描
                time.sleep(self.config["scan_interval"])
                
            except Exception as e:
                print(f"❌ 戰鬥循環錯誤: {e}")
                self.stats["errors"] += 1
                if self.callbacks["on_error"]:
                    self.callbacks["on_error"](e)
                time.sleep(1.0)
    
    def _find_and_attack_enemy(self) -> bool:
        """尋找並攻擊敵人"""
        if not self.templates["enemy"]:
            return False
        
        region = self.config["search_region"]
        
        # 遍歷所有敵人模板
        for enemy_template in self.templates["enemy"]:
            location = self.ir.find_image(enemy_template, region=region)
            
            if location:
                self.stats["enemies_found"] += 1
                print(f"🎯 發現敵人: {os.path.basename(enemy_template)}")
                
                # 回調
                if self.callbacks["on_enemy_found"]:
                    self.callbacks["on_enemy_found"](location)
                
                # 移動滑鼠到敵人
                center = self.ir.get_image_center(location)
                pyautogui.moveTo(center[0], center[1], duration=self.config["move_duration"])
                time.sleep(0.1)
                
                # 點擊敵人
                pyautogui.click()
                print(f"🖱️ 點擊敵人位置: {center}")
                
                # 執行攻擊序列
                self._attack_sequence()
                
                return True
        
        return False
    
    def _attack_sequence(self):
        """攻擊序列"""
        # 檢查技能是否可用
        for i, skill_template in enumerate(self.templates["skill_ready"]):
            if skill_template and self.ir.image_exists(skill_template):
                # 使用技能
                skill_key = self.config["skill_keys"][i] if i < len(self.config["skill_keys"]) else None
                if skill_key:
                    pyautogui.press(skill_key)
                    self.stats["skills_used"] += 1
                    print(f"⚡ 使用技能: {skill_key}")
                    
                    if self.callbacks["on_skill_used"]:
                        self.callbacks["on_skill_used"](skill_key)
                    
                    time.sleep(0.3)
        
        # 普通攻擊
        attack_key = self.config["attack_key"]
        pyautogui.press(attack_key)
        self.stats["attacks_made"] += 1
        print(f"⚔️ 普通攻擊: {attack_key}")
        
        if self.callbacks["on_attack"]:
            self.callbacks["on_attack"](attack_key)
        
        time.sleep(self.config["attack_delay"])
    
    def _check_low_hp(self) -> bool:
        """檢查血量是否過低"""
        if not self.templates["low_hp"]:
            return False
        
        return self.ir.image_exists(self.templates["low_hp"])
    
    def _handle_low_hp(self):
        """處理低血量"""
        print("❤️ 血量過低!")
        
        if self.callbacks["on_hp_low"]:
            self.callbacks["on_hp_low"]()
        
        # 預設行為: 暫停戰鬥
        self.pause()
    
    def _check_death(self) -> bool:
        """檢查是否死亡"""
        if not self.templates["dead"]:
            return False
        
        return self.ir.image_exists(self.templates["dead"])
    
    def _loot_items(self):
        """拾取物品"""
        if not self.templates["loot"]:
            return
        
        region = self.config["search_region"]
        
        for loot_template in self.templates["loot"]:
            location = self.ir.find_image(loot_template, region=region)
            
            if location:
                center = self.ir.get_image_center(location)
                pyautogui.moveTo(center[0], center[1], duration=self.config["move_duration"])
                time.sleep(0.1)
                pyautogui.click()
                
                self.stats["items_looted"] += 1
                print(f"💎 拾取物品: {os.path.basename(loot_template)}")
                
                if self.callbacks["on_loot"]:
                    self.callbacks["on_loot"](location)
                
                time.sleep(0.3)
    
    def _print_stats(self):
        """顯示統計"""
        print("\n" + "=" * 50)
        print("📊 戰鬥統計")
        print("=" * 50)
        print(f"運行時間: {self.stats['runtime']:.1f} 秒")
        print(f"發現敵人: {self.stats['enemies_found']} 次")
        print(f"攻擊次數: {self.stats['attacks_made']} 次")
        print(f"技能使用: {self.stats['skills_used']} 次")
        print(f"拾取物品: {self.stats['items_looted']} 個")
        print(f"錯誤次數: {self.stats['errors']} 次")
        print("=" * 50 + "\n")
    
    def get_stats(self) -> Dict:
        """取得統計數據"""
        if self.stats["start_time"]:
            self.stats["runtime"] = time.time() - self.stats["start_time"]
        return self.stats.copy()


# 簡易使用範例
if __name__ == "__main__":
    print("ChroLens 自動戰鬥系統測試")
    print("=" * 50)
    
    # 創建戰鬥系統
    combat = AutoCombatSystem()
    
    # 配置
    combat.set_config(
        attack_key="1",
        skill_keys=["q", "w", "e"],
        move_duration=0.3,
        attack_delay=0.5,
        scan_interval=1.0
    )
    
    # 設定圖片模板
    combat.set_templates(
        enemy=["enemy_goblin.png", "enemy_slime.png"],
        low_hp="hp_warning.png",
        skill_ready=["skill_q_ready.png", "skill_w_ready.png"],
        loot=["loot_gold.png", "loot_item.png"],
        dead="game_over.png"
    )
    
    # 設定回調
    def on_enemy_found(location):
        print(f"🎯 回調: 發現敵人於 {location}")
    
    def on_attack(key):
        print(f"⚔️ 回調: 攻擊按鍵 {key}")
    
    combat.set_callback("on_enemy_found", on_enemy_found)
    combat.set_callback("on_attack", on_attack)
    
    print("\n配置完成!")
    print("按 Enter 開始戰鬥 (Ctrl+C 停止)")
    input()
    
    # 啟動
    combat.start()
    
    try:
        while combat.is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止...")
        combat.stop()
