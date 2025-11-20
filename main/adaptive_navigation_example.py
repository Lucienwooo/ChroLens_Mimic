# -*- coding: utf-8 -*-
"""
自適應導航系統 - 使用範例
展示如何使用 AdaptiveNavigationSystem 進行自動探索和戰鬥
"""

from adaptive_navigation_system import AdaptiveNavigationSystem
import time

# ============================================
# 基礎使用範例
# ============================================

def basic_example():
    """基礎範例: 探索和學習地圖"""
    print("=" * 60)
    print("📖 基礎範例: 自動探索地圖")
    print("=" * 60)
    
    # 1. 創建導航系統
    nav = AdaptiveNavigationSystem()
    
    # 2. 鎖定遊戲視窗
    success = nav.lock_game_window("MapleStory")  # 替換為你的遊戲視窗標題
    if not success:
        print("❌ 無法鎖定遊戲視窗,請檢查視窗標題是否正確")
        return
    
    # 3. 設定角色識別模板
    nav.set_character_template("images/my_character.png")
    
    # 4. 啟動並探索
    nav.start()
    nav.explore_surroundings(duration=60)  # 探索60秒
    nav.stop()


# ============================================
# 進階範例: 自動打怪
# ============================================

def combat_example():
    """進階範例: 自動探索+戰鬥"""
    print("=" * 60)
    print("⚔️ 進階範例: 自動打怪")
    print("=" * 60)
    
    # 1. 創建導航系統並自訂配置
    custom_config = {
        'recognition_confidence': 0.8,  # 提高識別精確度
        'move_test_duration': 0.2,      # 縮短測試時間
        'move_keys': {
            'left': 'left',
            'right': 'right',
            'up': 'up',
            'down': 'down',
            'jump': 'alt',
            'attack': 'ctrl',
            'skill1': 'z',      # 第一個技能
            'skill2': 'x',      # 第二個技能
            'skill3': 'c',      # 第三個技能
            'hp_potion': 'pageup',
            'mp_potion': 'pagedown'
        }
    }
    
    nav = AdaptiveNavigationSystem(config=custom_config)
    
    # 2. 鎖定視窗
    nav.lock_game_window("你的遊戲")
    
    # 3. 設定角色和敵人模板
    nav.set_character_template("images/character.png")
    nav.add_enemy_template("蝸牛", "images/snail.png")
    nav.add_enemy_template("菇菇", "images/mushroom.png")
    nav.add_enemy_template("綠水靈", "images/slime.png")
    
    # 4. 設定優先攻擊目標 (按優先級)
    nav.set_priority_enemies(["菇菇", "綠水靈", "蝸牛"])
    
    # 5. 配置戰鬥參數
    nav.combat_config.update({
        'auto_attack': True,
        'attack_range': 150,
        'use_potions': True,
        'hp_potion_threshold': 0.6,  # 血量低於60%喝水
        'skill_cooldowns': {
            'z': 5.0,   # 技能1冷卻5秒
            'x': 8.0,   # 技能2冷卻8秒
            'c': 15.0   # 技能3冷卻15秒
        }
    })
    
    # 6. 設定回調函數
    def on_enemy_found(enemy):
        print(f"🎯 發現目標: {enemy.enemy_type} at ({enemy.position.x}, {enemy.position.y})")
    
    def on_hp_low(hp):
        print(f"⚠️ 血量過低: {hp*100:.1f}%")
    
    def on_stuck(position):
        print(f"🆘 角色卡住了! 位置: ({position.x}, {position.y})")
    
    nav.set_callback('on_enemy_detected', on_enemy_found)
    nav.set_callback('on_hp_low', on_hp_low)
    nav.set_callback('on_stuck', on_stuck)
    
    # 7. 啟動自動打怪
    nav.start()
    nav.explore_surroundings(duration=300, auto_combat=True)  # 5分鐘
    nav.stop()


# ============================================
# 持久化範例: 載入已學習的地圖
# ============================================

def persistence_example():
    """持久化範例: 使用之前學習的地圖"""
    print("=" * 60)
    print("💾 持久化範例: 載入已學習地圖")
    print("=" * 60)
    
    # 1. 創建導航系統
    nav = AdaptiveNavigationSystem()
    nav.lock_game_window("你的遊戲")
    
    # 2. 載入之前學習的地圖數據
    nav.load_map_data("learned_map.json")
    
    # 3. 設定模板
    nav.set_character_template("images/character.png")
    nav.add_enemy_template("怪物A", "images/enemy_a.png")
    
    # 4. 繼續探索 (會利用之前的知識)
    nav.start()
    nav.explore_surroundings(duration=120, auto_combat=True)
    nav.stop()


# ============================================
# 自訂控制範例
# ============================================

def custom_control_example():
    """自訂控制範例: 手動控制探索流程"""
    print("=" * 60)
    print("🎮 自訂控制範例")
    print("=" * 60)
    
    nav = AdaptiveNavigationSystem()
    nav.lock_game_window("你的遊戲")
    nav.set_character_template("images/character.png")
    nav.add_enemy_template("目標怪", "images/target.png")
    
    nav.start()
    
    # 自訂控制循環
    for i in range(10):
        print(f"\n--- 循環 {i+1}/10 ---")
        
        # 1. 找到角色位置
        pos = nav.find_character_position()
        if pos:
            print(f"📍 角色位置: ({pos.x}, {pos.y})")
        
        # 2. 學習當前地形
        terrain = nav.learn_current_terrain()
        print(f"🗺️ 地形類型: {terrain.terrain_type}")
        
        # 3. 偵測敵人
        enemies = nav.detect_enemies()
        if enemies:
            print(f"🎯 發現 {len(enemies)} 個敵人")
            
            # 攻擊最近的敵人
            target = nav.find_nearest_enemy()
            if target:
                nav.attack_enemy(target)
        
        # 4. 移動到下一個位置
        if terrain.can_walk_right:
            nav.move_direction('right', duration=1.0)
        elif terrain.can_walk_left:
            nav.move_direction('left', duration=1.0)
        
        time.sleep(1)
    
    nav.stop()


# ============================================
# 純戰鬥模式範例
# ============================================

def pure_combat_example():
    """純戰鬥模式: 在當前位置持續打怪"""
    print("=" * 60)
    print("⚔️ 純戰鬥模式")
    print("=" * 60)
    
    nav = AdaptiveNavigationSystem()
    nav.lock_game_window("你的遊戲")
    nav.set_character_template("images/character.png")
    nav.add_enemy_template("怪物", "images/enemy.png")
    
    # 配置戰鬥
    nav.combat_config.update({
        'auto_attack': True,
        'attack_range': 200,
        'use_potions': True,
        'hp_potion_threshold': 0.5
    })
    
    nav.start()
    nav.combat_loop(duration=120)  # 戰鬥2分鐘
    nav.stop()


# ============================================
# 配置測試範例
# ============================================

def config_test_example():
    """配置測試: 測試各種配置參數"""
    print("=" * 60)
    print("🔧 配置測試")
    print("=" * 60)
    
    nav = AdaptiveNavigationSystem()
    
    # 顯示預設配置
    print("\n📋 預設配置:")
    config = nav.get_config()
    for key, value in config.items():
        print(f"   {key}: {value}")
    
    # 更新配置
    nav.update_config({
        'recognition_confidence': 0.9,
        'move_test_duration': 0.15,
        'exploration_priority': ['up', 'right', 'left', 'down']
    })
    
    # 鎖定視窗並測試
    if nav.lock_game_window("你的遊戲"):
        nav.set_character_template("images/character.png")
        
        # 測試移動
        print("\n🧪 測試移動:")
        for direction in ['left', 'right', 'jump', 'up', 'down']:
            result = nav.test_movement(direction)
            print(f"   {direction}: {'✅ 可行' if result else '❌ 不可行'}")


# ============================================
# 快速開始範例
# ============================================

def quick_start():
    """快速開始: 最簡單的使用方式"""
    print("=" * 60)
    print("🚀 快速開始")
    print("=" * 60)
    
    # 創建並配置
    nav = AdaptiveNavigationSystem()
    nav.lock_game_window("MapleStory")  # 你的遊戲視窗名
    nav.set_character_template("images/char.png")
    nav.add_enemy_template("怪", "images/enemy.png")
    
    # 一鍵啟動
    nav.start()
    nav.explore_surroundings(duration=180, auto_combat=True)
    nav.stop()


# ============================================
# 主程式
# ============================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🎮 ChroLens 自適應導航系統 - 範例集")
    print("=" * 60)
    print("\n選擇範例:")
    print("1. 基礎範例 - 探索地圖")
    print("2. 進階範例 - 自動打怪")
    print("3. 持久化範例 - 載入已學習地圖")
    print("4. 自訂控制範例")
    print("5. 純戰鬥模式")
    print("6. 配置測試")
    print("7. 快速開始")
    
    try:
        choice = input("\n請選擇 (1-7): ").strip()
        
        examples = {
            '1': basic_example,
            '2': combat_example,
            '3': persistence_example,
            '4': custom_control_example,
            '5': pure_combat_example,
            '6': config_test_example,
            '7': quick_start
        }
        
        func = examples.get(choice)
        if func:
            print("\n")
            func()
        else:
            print("❌ 無效選擇")
    
    except KeyboardInterrupt:
        print("\n\n⏹️ 使用者中斷")
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
