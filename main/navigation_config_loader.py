# -*- coding: utf-8 -*-
"""
配置載入工具
從 JSON 檔案載入並應用導航系統配置
"""

import json
import os
from typing import Dict
from adaptive_navigation_system import AdaptiveNavigationSystem


def load_config_from_file(filepath: str = "navigation_config.json") -> Dict:
    """
    從 JSON 檔案載入配置
    :param filepath: 配置檔案路徑
    :return: 配置字典
    """
    if not os.path.exists(filepath):
        print(f"⚠️ 找不到配置檔案: {filepath}")
        print("   將使用預設配置")
        return {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 轉換為系統可用的配置格式
        config = {}
        
        # 識別設定
        if '識別設定' in data:
            recog = data['識別設定']
            config['recognition_confidence'] = recog.get('recognition_confidence', 0.75)
            config['multi_scale_search'] = recog.get('multi_scale_search', True)
            scale_range = recog.get('scale_range', [0.8, 1.2, 0.1])
            config['scale_range'] = tuple(scale_range)
        
        # 按鍵設定
        if '按鍵設定' in data:
            config['move_keys'] = data['按鍵設定']['move_keys']
        
        # 移動測試設定
        if '移動測試設定' in data:
            test = data['移動測試設定']
            config['move_test_duration'] = test.get('move_test_duration', 0.3)
            config['movement_threshold'] = test.get('movement_threshold', 10)
            config['position_similarity_threshold'] = test.get('position_similarity_threshold', 20)
        
        # 探索設定
        if '探索設定' in data:
            explore = data['探索設定']
            config['exploration_priority'] = explore.get('exploration_priority', ['right', 'left', 'up', 'down'])
            config['revisit_threshold'] = explore.get('revisit_threshold', 3)
            config['exploration_timeout'] = explore.get('exploration_timeout', 300)
        
        # 性能設定
        if '性能設定' in data:
            perf = data['性能設定']
            config['screenshot_interval'] = perf.get('screenshot_interval', 0.1)
            config['cache_screenshots'] = perf.get('cache_screenshots', True)
            config['max_cache_size'] = perf.get('max_cache_size', 10)
        
        print(f"✅ 已載入配置: {filepath}")
        return config
    
    except Exception as e:
        print(f"❌ 載入配置失敗: {e}")
        return {}


def create_navigation_from_config(filepath: str = "navigation_config.json") -> AdaptiveNavigationSystem:
    """
    從配置檔案創建並配置導航系統
    :param filepath: 配置檔案路徑
    :return: 配置好的 AdaptiveNavigationSystem 實例
    """
    # 載入配置檔案
    if not os.path.exists(filepath):
        print(f"❌ 找不到配置檔案: {filepath}")
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 載入系統配置
    config = load_config_from_file(filepath)
    
    # 創建導航系統
    nav = AdaptiveNavigationSystem(config=config)
    
    # 鎖定遊戲視窗
    if '遊戲設定' in data:
        window_title = data['遊戲設定'].get('window_title')
        if window_title:
            success = nav.lock_game_window(window_title)
            if not success:
                print(f"⚠️ 無法鎖定視窗: {window_title}")
    
    # 設定角色模板
    if '識別設定' in data:
        recog = data['識別設定']
        
        # 角色模板
        char_template = recog.get('character_template')
        if char_template and os.path.exists(char_template):
            nav.set_character_template(char_template)
        else:
            print(f"⚠️ 找不到角色模板: {char_template}")
        
        # 敵人模板
        enemy_templates = recog.get('enemy_templates', {})
        for enemy_type, template_path in enemy_templates.items():
            if os.path.exists(template_path):
                nav.add_enemy_template(enemy_type, template_path)
            else:
                print(f"⚠️ 找不到敵人模板: {enemy_type} -> {template_path}")
    
    # 設定戰鬥配置
    if '戰鬥設定' in data:
        combat = data['戰鬥設定']
        
        nav.combat_config.update({
            'auto_attack': combat.get('auto_attack', True),
            'attack_range': combat.get('attack_range', 100),
            'use_potions': combat.get('use_potions', True),
            'hp_potion_threshold': combat.get('hp_potion_threshold', 0.5),
            'mp_potion_threshold': combat.get('mp_potion_threshold', 0.3),
            'skill_cooldowns': combat.get('skill_cooldowns', {})
        })
        
        # 優先敵人
        priority = combat.get('priority_enemies', [])
        if priority:
            nav.set_priority_enemies(priority)
    
    # 設定安全配置
    if '安全設定' in data:
        safety = data['安全設定']
        nav.safety_config.update({
            'stuck_detection': safety.get('stuck_detection', True),
            'stuck_threshold': safety.get('stuck_threshold', 5),
            'emergency_escape': safety.get('emergency_escape', True),
            'max_death_count': safety.get('max_death_count', 3)
        })
    
    print("✅ 導航系統配置完成")
    return nav


def save_config_template(filepath: str = "navigation_config_template.json"):
    """
    儲存配置模板
    :param filepath: 儲存路徑
    """
    template = {
        "說明": "ChroLens 自適應導航系統配置檔案",
        "version": "1.0",
        
        "遊戲設定": {
            "window_title": "你的遊戲視窗標題",
            "說明": "使用工作管理員查看遊戲的視窗標題"
        },
        
        "識別設定": {
            "character_template": "images/character.png",
            "enemy_templates": {
                "怪物1": "images/enemy1.png",
                "怪物2": "images/enemy2.png"
            },
            "recognition_confidence": 0.75
        },
        
        "按鍵設定": {
            "move_keys": {
                "left": "left",
                "right": "right",
                "up": "up",
                "down": "down",
                "jump": "alt",
                "attack": "ctrl",
                "skill1": "a",
                "skill2": "s",
                "hp_potion": "pageup"
            }
        },
        
        "戰鬥設定": {
            "auto_attack": True,
            "attack_range": 100,
            "use_potions": True,
            "hp_potion_threshold": 0.5
        }
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 配置模板已儲存: {filepath}")


# ============================================
# 快速啟動函數
# ============================================

def quick_start_from_config(config_file: str = "navigation_config.json",
                            duration: int = 300,
                            auto_combat: bool = True):
    """
    從配置檔案快速啟動
    :param config_file: 配置檔案路徑
    :param duration: 運行時長(秒)
    :param auto_combat: 是否自動戰鬥
    """
    print("=" * 60)
    print("🚀 ChroLens 自適應導航系統 - 快速啟動")
    print("=" * 60)
    
    # 創建並配置系統
    nav = create_navigation_from_config(config_file)
    
    if not nav:
        print("❌ 系統初始化失敗")
        return
    
    # 顯示配置摘要
    print("\n📋 當前配置:")
    print(f"   識別信心度: {nav.config['recognition_confidence']}")
    print(f"   移動測試時長: {nav.move_test_duration}s")
    print(f"   探索優先級: {nav.config['exploration_priority']}")
    print(f"   自動戰鬥: {'開啟' if auto_combat else '關閉'}")
    print(f"   運行時長: {duration}秒 ({duration//60}分鐘)")
    
    # 等待用戶確認
    print("\n" + "=" * 60)
    input("按 Enter 開始運行,或 Ctrl+C 取消...")
    
    try:
        # 啟動
        nav.start()
        nav.explore_surroundings(duration=duration, auto_combat=auto_combat)
        nav.stop()
        
        print("\n✅ 運行完成!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 使用者中斷")
        nav.stop()
    
    except Exception as e:
        print(f"\n❌ 運行錯誤: {e}")
        nav.stop()


# ============================================
# 主程式
# ============================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 命令列模式
        command = sys.argv[1]
        
        if command == "start":
            # 快速啟動
            config_file = sys.argv[2] if len(sys.argv) > 2 else "navigation_config.json"
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else 300
            quick_start_from_config(config_file, duration)
        
        elif command == "template":
            # 生成模板
            output = sys.argv[2] if len(sys.argv) > 2 else "navigation_config_template.json"
            save_config_template(output)
        
        else:
            print(f"❌ 未知命令: {command}")
            print("可用命令:")
            print("  python navigation_config_loader.py start [配置檔案] [時長秒數]")
            print("  python navigation_config_loader.py template [輸出檔案]")
    
    else:
        # 互動模式
        print("=" * 60)
        print("🎮 ChroLens 導航系統 - 配置工具")
        print("=" * 60)
        print("\n選擇操作:")
        print("1. 從配置檔案啟動")
        print("2. 生成配置模板")
        print("3. 測試配置載入")
        
        choice = input("\n請選擇 (1-3): ").strip()
        
        if choice == '1':
            config_file = input("配置檔案路徑 [navigation_config.json]: ").strip()
            if not config_file:
                config_file = "navigation_config.json"
            
            duration = input("運行時長(秒) [300]: ").strip()
            duration = int(duration) if duration else 300
            
            auto_combat = input("自動戰鬥? (y/n) [y]: ").strip().lower()
            auto_combat = auto_combat != 'n'
            
            quick_start_from_config(config_file, duration, auto_combat)
        
        elif choice == '2':
            output = input("輸出檔案名 [navigation_config_template.json]: ").strip()
            if not output:
                output = "navigation_config_template.json"
            save_config_template(output)
        
        elif choice == '3':
            config_file = input("配置檔案路徑 [navigation_config.json]: ").strip()
            if not config_file:
                config_file = "navigation_config.json"
            
            config = load_config_from_file(config_file)
            print("\n📋 載入的配置:")
            for key, value in config.items():
                print(f"   {key}: {value}")
        
        else:
            print("❌ 無效選擇")
