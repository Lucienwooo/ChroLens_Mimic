
# -*- coding: utf-8 -*-
"""
ChroLens 自適應導航系統 (Adaptive Navigation System)
透過實際移動嘗試來學習地圖、地形和怪物分布

核心概念:
1. 鎖定遊戲視窗
2. 實際嘗試各種移動 (左/右/上/下/跳躍)
3. 透過螢幕變化判斷移動是否成功
4. 建立地圖知識庫
5. 偵測並記錄怪物位置
"""

import cv2
import numpy as np
import pyautogui
import time
import json
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import deque
from image_recognition import ImageRecognition
import win32gui
import win32con


@dataclass
class Position:
    """位置數據"""
    x: int
    y: int
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def distance_to(self, other: 'Position') -> float:
        """計算到另一位置的距離"""
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5
    
    def to_dict(self):
        return {'x': self.x, 'y': self.y}


@dataclass
class TerrainInfo:
    """地形資訊"""
    terrain_type: str  # 'ground', 'ladder', 'rope', 'platform', 'obstacle'
    can_walk_left: bool = False
    can_walk_right: bool = False
    can_jump: bool = False
    can_climb_up: bool = False
    can_climb_down: bool = False
    tested: bool = False
    
    def to_dict(self):
        return asdict(self)


@dataclass
class EnemyInfo:
    """敵人資訊"""
    enemy_type: str
    position: Position
    first_seen: float
    last_seen: float
    is_moving: bool = False
    health_status: str = 'unknown'  # 'full', 'medium', 'low', 'unknown'
    
    def to_dict(self):
        return {
            'enemy_type': self.enemy_type,
            'position': self.position.to_dict(),
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'is_moving': self.is_moving,
            'health_status': self.health_status
        }


class AdaptiveNavigationSystem:
    """自適應導航系統 - 透過實際移動學習環境"""
    
    def __init__(self, game_window_title: str = None, config: Dict = None):
        """
        初始化
        :param game_window_title: 遊戲視窗標題 (用於鎖定視窗)
        :param config: 配置字典 (可選)
        """
        self.game_window_title = game_window_title
        self.game_hwnd = None
        self.game_rect = None
        
        # 載入配置
        self.config = self._load_default_config()
        if config:
            self.config.update(config)
        
        # 圖片識別
        self.ir = ImageRecognition(confidence=self.config['recognition_confidence'])
        
        # 地圖知識庫
        self.map_data: Dict[Tuple[int, int], TerrainInfo] = {}
        self.explored_positions = set()
        self.current_position: Optional[Position] = None
        
        # 敵人追蹤
        self.enemies: List[EnemyInfo] = []
        self.enemy_templates = {}  # {enemy_type: template_path}
        self.priority_enemies = []  # 優先攻擊的敵人類型
        
        # 角色識別
        self.character_template = None
        self.character_position: Optional[Position] = None
        self.character_hp_region = None  # 血量偵測區域
        
        # 移動參數
        self.move_keys = self.config['move_keys'].copy()
        
        # 學習參數
        self.move_test_duration = self.config['move_test_duration']
        self.movement_threshold = self.config['movement_threshold']
        self.exploration_history = deque(maxlen=100)
        
        # 戰鬥參數
        self.combat_config = {
            'auto_attack': True,
            'attack_range': 100,  # 攻擊範圍(像素)
            'skill_cooldowns': {},  # {skill_key: cooldown_time}
            'last_skill_use': {},   # {skill_key: last_use_time}
            'use_potions': True,
            'hp_potion_threshold': 0.5,  # 血量低於50%喝水
            'mp_potion_threshold': 0.3   # 魔力低於30%喝藍
        }
        
        # 安全機制
        self.safety_config = {
            'stuck_detection': True,
            'stuck_threshold': 5,  # 連續5次無法移動視為卡住
            'stuck_counter': 0,
            'emergency_escape': True,
            'max_death_count': 3,  # 死亡3次後停止
            'death_count': 0
        }
        
        # 統計數據
        self.stats = {
            'exploration_time': 0,
            'positions_explored': 0,
            'enemies_found': 0,
            'enemies_killed': 0,
            'deaths': 0,
            'stuck_events': 0,
            'start_time': None
        }
        
        # 狀態
        self.is_running = False
        self.learning_mode = True  # 學習模式:主動探索地圖
        self.combat_mode = False   # 戰鬥模式
        
        # 回調函數
        self.callbacks = {
            'on_terrain_learned': None,
            'on_enemy_detected': None,
            'on_position_updated': None,
            'on_stuck': None,
            'on_death': None,
            'on_hp_low': None,
            'on_stats_update': None
        }
        
        print("✅ 自適應導航系統已初始化")
        print(f"   識別信心度: {self.config['recognition_confidence']}")
        print(f"   移動測試時長: {self.move_test_duration}s")
    
    def _load_default_config(self) -> Dict:
        """載入預設配置"""
        return {
            # 識別參數
            'recognition_confidence': 0.75,
            'multi_scale_search': True,
            'scale_range': (0.8, 1.2, 0.1),  # (最小, 最大, 步進)
            
            # 移動參數
            'move_keys': {
                'left': 'left',
                'right': 'right',
                'up': 'up',
                'down': 'down',
                'jump': 'alt',
                'attack': 'ctrl',
                'skill1': 'a',
                'skill2': 's',
                'skill3': 'd',
                'skill4': 'f',
                'hp_potion': 'pageup',
                'mp_potion': 'pagedown'
            },
            
            # 測試參數
            'move_test_duration': 0.3,
            'movement_threshold': 10,
            'position_similarity_threshold': 20,  # 位置相似度(像素)
            
            # 探索參數
            'exploration_priority': ['right', 'left', 'up', 'down'],
            'revisit_threshold': 3,  # 同一位置重複訪問幾次後降低優先級
            'exploration_timeout': 300,  # 探索超時(秒)
            
            # 性能參數
            'screenshot_interval': 0.1,  # 截圖間隔
            'cache_screenshots': True,
            'max_cache_size': 10
        }
    
    # ============================================
    # 視窗管理
    # ============================================
    
    def lock_game_window(self, window_title: str = None) -> bool:
        """
        鎖定遊戲視窗
        :param window_title: 視窗標題 (可選)
        :return: 是否成功鎖定
        """
        if window_title:
            self.game_window_title = window_title
        
        if not self.game_window_title:
            print("❌ 未指定視窗標題")
            return False
        
        # 查找視窗
        self.game_hwnd = win32gui.FindWindow(None, self.game_window_title)
        
        if not self.game_hwnd:
            print(f"❌ 找不到視窗: {self.game_window_title}")
            return False
        
        # 取得視窗位置
        self.game_rect = win32gui.GetWindowRect(self.game_hwnd)
        print(f"✅ 已鎖定視窗: {self.game_window_title}")
        print(f"   位置: {self.game_rect}")
        
        # 將視窗置頂
        win32gui.SetForegroundWindow(self.game_hwnd)
        
        return True
    
    def capture_game_screen(self, cache: bool = None) -> Optional[np.ndarray]:
        """
        截取遊戲視窗畫面
        :param cache: 是否使用快取 (預設使用配置)
        :return: OpenCV 圖片陣列
        """
        if not self.game_rect:
            return None
        
        # 檢查快取
        use_cache = cache if cache is not None else self.config['cache_screenshots']
        if use_cache and hasattr(self, '_screenshot_cache'):
            cache_time, cached_img = self._screenshot_cache
            if time.time() - cache_time < self.config['screenshot_interval']:
                return cached_img.copy()
        
        left, top, right, bottom = self.game_rect
        width = right - left
        height = bottom - top
        
        # 截圖
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # 更新快取
        if use_cache:
            self._screenshot_cache = (time.time(), screenshot)
        
        return screenshot
    
    def get_game_region(self, region_name: str) -> Optional[Tuple[int, int, int, int]]:
        """
        取得遊戲特定區域的座標
        :param region_name: 區域名稱 ('hp', 'mp', 'minimap', 'chat', 'inventory')
        :return: (x, y, width, height)
        """
        if not self.game_rect:
            return None
        
        left, top, right, bottom = self.game_rect
        width = right - left
        height = bottom - top
        
        # 預設區域配置 (可根據遊戲調整)
        regions = {
            'hp': (left + 20, top + 20, 150, 20),      # 左上角血條
            'mp': (left + 20, top + 45, 150, 20),      # 左上角魔條
            'minimap': (right - 200, top + 20, 180, 180),  # 右上角小地圖
            'chat': (left + 20, bottom - 200, 400, 180),   # 左下角聊天框
            'inventory': (right - 220, bottom - 400, 200, 380),  # 右下角背包
            'buff': (left + 200, top + 20, 300, 40),   # 上方Buff欄
        }
        
        return regions.get(region_name)
    
    # ============================================
    # 角色定位
    # ============================================
    
    def set_character_template(self, template_path: str):
        """設定角色識別模板"""
        self.character_template = template_path
        print(f"✅ 已設定角色模板: {template_path}")
    
    def find_character_position(self) -> Optional[Position]:
        """
        找到角色在畫面中的位置
        :return: 角色位置
        """
        if not self.character_template:
            print("⚠️ 未設定角色模板")
            return None
        
        # 截取遊戲畫面
        screenshot = self.capture_game_screen()
        if screenshot is None:
            return None
        
        # 尋找角色
        location = self.ir.find_image(self.character_template)
        
        if location:
            x, y, w, h = location
            center_x = x + w // 2
            center_y = y + h // 2
            self.character_position = Position(center_x, center_y)
            return self.character_position
        
        return None
    
    # ============================================
    # 移動測試與學習
    # ============================================
    
    def test_movement(self, direction: str) -> bool:
        """
        測試某個方向的移動是否可行
        :param direction: 'left', 'right', 'up', 'down', 'jump'
        :return: 移動是否成功
        """
        # 截取移動前的畫面
        before = self.capture_game_screen()
        if before is None:
            return False
        
        # 執行移動
        key = self.move_keys.get(direction)
        if not key:
            return False
        
        pyautogui.keyDown(key)
        time.sleep(self.move_test_duration)
        pyautogui.keyUp(key)
        
        # 等待一下讓畫面穩定
        time.sleep(0.1)
        
        # 截取移動後的畫面
        after = self.capture_game_screen()
        if after is None:
            return False
        
        # 比較畫面差異
        diff = cv2.absdiff(before, after)
        total_diff = np.sum(diff)
        
        # 如果差異大於閾值,表示移動成功
        success = total_diff > self.movement_threshold * 1000000
        
        if success:
            print(f"✅ {direction} 方向可移動 (差異: {total_diff})")
        else:
            print(f"❌ {direction} 方向無法移動 (差異: {total_diff})")
        
        return success
    
    def learn_current_terrain(self) -> TerrainInfo:
        """
        學習當前位置的地形資訊
        透過測試各個方向來了解地形特性
        """
        print("\n🔍 開始學習當前地形...")
        
        terrain = TerrainInfo(terrain_type='unknown')
        
        # 測試左右移動
        terrain.can_walk_left = self.test_movement('left')
        time.sleep(0.2)
        terrain.can_walk_right = self.test_movement('right')
        time.sleep(0.2)
        
        # 測試跳躍
        terrain.can_jump = self.test_movement('jump')
        time.sleep(0.2)
        
        # 測試爬升/下降
        terrain.can_climb_up = self.test_movement('up')
        time.sleep(0.2)
        terrain.can_climb_down = self.test_movement('down')
        time.sleep(0.2)
        
        # 根據測試結果判斷地形類型
        if terrain.can_climb_up or terrain.can_climb_down:
            terrain.terrain_type = 'ladder'  # 樓梯或繩索
        elif not terrain.can_walk_left and not terrain.can_walk_right:
            terrain.terrain_type = 'obstacle'  # 障礙物
        elif terrain.can_jump:
            terrain.terrain_type = 'ground'  # 地面
        else:
            terrain.terrain_type = 'platform'  # 平台
        
        terrain.tested = True
        
        print(f"📊 地形學習完成: {terrain.terrain_type}")
        print(f"   左:{terrain.can_walk_left} 右:{terrain.can_walk_right} 跳:{terrain.can_jump}")
        print(f"   上爬:{terrain.can_climb_up} 下爬:{terrain.can_climb_down}")
        
        # 儲存到地圖
        if self.character_position:
            pos_key = (self.character_position.x, self.character_position.y)
            self.map_data[pos_key] = terrain
            self.explored_positions.add(pos_key)
        
        # 回調
        if self.callbacks['on_terrain_learned']:
            self.callbacks['on_terrain_learned'](terrain)
        
        return terrain
    
    def explore_surroundings(self, duration: int = 60, auto_combat: bool = True):
        """
        探索周圍環境
        :param duration: 探索持續時間(秒)
        :param auto_combat: 是否自動戰鬥
        """
        print(f"\n🗺️ 開始探索環境 (持續 {duration} 秒)...")
        print(f"   自動戰鬥: {'開啟' if auto_combat else '關閉'}")
        
        self.stats['start_time'] = time.time()
        start_time = time.time()
        exploration_count = 0
        last_stats_update = time.time()
        
        while time.time() - start_time < duration and self.is_running:
            try:
                # 1. 定位角色
                char_pos = self.find_character_position()
                if not char_pos:
                    print("⚠️ 找不到角色,等待中...")
                    time.sleep(1)
                    continue
                
                # 記錄位置歷史
                self.exploration_history.append(char_pos)
                
                # 2. 檢查血量
                hp = self.detect_hp()
                if hp and hp < self.combat_config['hp_potion_threshold']:
                    self.use_potion('hp')
                
                # 3. 卡住偵測
                if self.detect_stuck():
                    self.escape_stuck()
                    continue
                
                # 4. 偵測敵人
                enemies = self.detect_enemies()
                
                # 5. 自動戰鬥
                if auto_combat and enemies:
                    target = self.find_nearest_enemy()
                    if target:
                        self.attack_enemy(target)
                        time.sleep(0.2)
                        continue
                
                # 6. 檢查是否已探索過這個位置
                pos_key = (char_pos.x, char_pos.y)
                if pos_key not in self.explored_positions:
                    # 學習當前地形
                    terrain = self.learn_current_terrain()
                    exploration_count += 1
                else:
                    # 已探索過,快速偵測
                    terrain = self.map_data.get(pos_key)
                
                # 7. 選擇下一個探索方向
                next_direction = self._choose_exploration_direction(char_pos, terrain)
                if next_direction:
                    self.move_direction(next_direction, duration=0.8)
                else:
                    # 沒有可探索的方向,隨機移動
                    import random
                    direction = random.choice(self.config['exploration_priority'][:2])
                    self.move_direction(direction, duration=0.5)
                
                # 8. 定期更新統計
                if time.time() - last_stats_update > 10:
                    self.update_stats()
                    last_stats_update = time.time()
                
                time.sleep(0.3)
                
            except Exception as e:
                print(f"❌ 探索過程錯誤: {e}")
                time.sleep(1)
        
        print(f"\n✅ 探索完成!")
        self.update_stats()
        self.print_stats()
    
    def _choose_exploration_direction(self, current_pos: Position, terrain: Optional[TerrainInfo]) -> Optional[str]:
        """
        選擇探索方向
        :param current_pos: 當前位置
        :param terrain: 當前地形
        :return: 方向字串
        """
        if not terrain:
            return None
        
        # 按優先級檢查可行方向
        for direction in self.config['exploration_priority']:
            # 檢查該方向是否可行
            can_move = False
            if direction == 'left' and terrain.can_walk_left:
                can_move = True
            elif direction == 'right' and terrain.can_walk_right:
                can_move = True
            elif direction == 'up' and terrain.can_climb_up:
                can_move = True
            elif direction == 'down' and terrain.can_climb_down:
                can_move = True
            
            # 檢查該方向是否已探索
            if can_move and not self._is_explored(current_pos, direction):
                return direction
        
        # 所有方向都探索過,返回可行的第一個方向
        if terrain.can_walk_right:
            return 'right'
        elif terrain.can_walk_left:
            return 'left'
        
        return None
    
    def _is_explored(self, pos: Position, direction: str) -> bool:
        """檢查某個方向是否已探索"""
        offset = 50  # 像素偏移
        if direction == 'left':
            check_pos = (pos.x - offset, pos.y)
        elif direction == 'right':
            check_pos = (pos.x + offset, pos.y)
        elif direction == 'up':
            check_pos = (pos.x, pos.y - offset)
        elif direction == 'down':
            check_pos = (pos.x, pos.y + offset)
        else:
            return True
        
        return check_pos in self.explored_positions
    
    def move_direction(self, direction: str, duration: float = 0.5):
        """執行移動"""
        key = self.move_keys.get(direction)
        if key:
            pyautogui.keyDown(key)
            time.sleep(duration)
            pyautogui.keyUp(key)
    
    # ============================================
    # 敵人偵測
    # ============================================
    
    def add_enemy_template(self, enemy_type: str, template_path: str):
        """
        添加敵人識別模板
        :param enemy_type: 敵人類型 (如 'A怪', 'B怪')
        :param template_path: 模板圖片路徑
        """
        self.enemy_templates[enemy_type] = template_path
        print(f"✅ 已添加敵人模板: {enemy_type} -> {template_path}")
    
    def detect_enemies(self) -> List[EnemyInfo]:
        """
        偵測畫面中的敵人
        :return: 偵測到的敵人列表
        """
        if not self.enemy_templates:
            return []
        
        detected = []
        current_time = time.time()
        
        for enemy_type, template_path in self.enemy_templates.items():
            # 尋找所有符合的敵人
            locations = self.ir.find_all_images(template_path, confidence=0.7)
            
            for loc in locations:
                x, y, w, h = loc
                center_x = x + w // 2
                center_y = y + h // 2
                position = Position(center_x, center_y)
                
                # 檢查是否已記錄
                existing = self._find_existing_enemy(position, enemy_type)
                if existing:
                    existing.last_seen = current_time
                else:
                    enemy = EnemyInfo(
                        enemy_type=enemy_type,
                        position=position,
                        first_seen=current_time,
                        last_seen=current_time
                    )
                    self.enemies.append(enemy)
                    detected.append(enemy)
                    
                    print(f"🎯 發現敵人: {enemy_type} at ({center_x}, {center_y})")
                    
                    if self.callbacks['on_enemy_detected']:
                        self.callbacks['on_enemy_detected'](enemy)
        
        # 清理過期敵人 (超過5秒未見)
        self.enemies = [e for e in self.enemies if current_time - e.last_seen < 5.0]
        
        return detected
    
    def _find_existing_enemy(self, position: Position, enemy_type: str) -> Optional[EnemyInfo]:
        """查找已存在的敵人"""
        for enemy in self.enemies:
            if enemy.enemy_type == enemy_type and enemy.position.distance_to(position) < 30:
                return enemy
        return None
    
    def find_nearest_enemy(self, enemy_type: str = None) -> Optional[EnemyInfo]:
        """
        找到最近的敵人
        :param enemy_type: 指定敵人類型 (可選)
        :return: 最近的敵人
        """
        if not self.character_position or not self.enemies:
            return None
        
        candidates = self.enemies
        if enemy_type:
            candidates = [e for e in self.enemies if e.enemy_type == enemy_type]
        
        if not candidates:
            return None
        
        # 優先考慮優先級敵人
        if self.priority_enemies:
            priority_candidates = [e for e in candidates if e.enemy_type in self.priority_enemies]
            if priority_candidates:
                candidates = priority_candidates
        
        nearest = min(candidates, 
                     key=lambda e: self.character_position.distance_to(e.position))
        
        return nearest
    
    # ============================================
    # 智能戰鬥系統
    # ============================================
    
    def detect_hp(self) -> Optional[float]:
        """
        偵測角色血量百分比
        :return: 血量百分比 (0.0-1.0)
        """
        hp_region = self.get_game_region('hp')
        if not hp_region:
            return None
        
        x, y, w, h = hp_region
        screenshot = self.capture_game_screen()
        if screenshot is None:
            return None
        
        # 截取血條區域
        hp_bar = screenshot[y:y+h, x:x+w]
        
        # 轉換為HSV (血條通常是紅色)
        hsv = cv2.cvtColor(hp_bar, cv2.COLOR_BGR2HSV)
        
        # 紅色範圍 (兩段,因為紅色跨越0度)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        
        # 創建遮罩
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        # 計算紅色像素比例
        red_pixels = np.count_nonzero(mask)
        total_pixels = w * h
        hp_percent = red_pixels / total_pixels if total_pixels > 0 else 0
        
        return min(1.0, max(0.0, hp_percent))
    
    def use_skill(self, skill_key: str, force: bool = False) -> bool:
        """
        使用技能
        :param skill_key: 技能按鍵
        :param force: 強制使用 (忽略冷卻)
        :return: 是否成功使用
        """
        current_time = time.time()
        
        # 檢查冷卻時間
        if not force:
            cooldown = self.combat_config['skill_cooldowns'].get(skill_key, 0)
            last_use = self.combat_config['last_skill_use'].get(skill_key, 0)
            if current_time - last_use < cooldown:
                return False
        
        # 執行技能
        pyautogui.press(skill_key)
        self.combat_config['last_skill_use'][skill_key] = current_time
        
        print(f"⚔️ 使用技能: {skill_key}")
        return True
    
    def use_potion(self, potion_type: str = 'hp') -> bool:
        """
        使用藥水
        :param potion_type: 'hp' 或 'mp'
        :return: 是否成功使用
        """
        if not self.combat_config['use_potions']:
            return False
        
        key = self.move_keys.get(f'{potion_type}_potion')
        if not key:
            return False
        
        pyautogui.press(key)
        print(f"💊 使用{potion_type.upper()}藥水")
        return True
    
    def attack_enemy(self, enemy: EnemyInfo) -> bool:
        """
        攻擊敵人
        :param enemy: 敵人資訊
        :return: 是否開始攻擊
        """
        if not self.character_position:
            return False
        
        # 計算距離
        distance = self.character_position.distance_to(enemy.position)
        
        # 如果距離太遠,先移動靠近
        if distance > self.combat_config['attack_range']:
            return self.move_to_position(enemy.position)
        
        # 面向敵人
        if enemy.position.x < self.character_position.x:
            self.move_direction('left', duration=0.1)
        else:
            self.move_direction('right', duration=0.1)
        
        # 攻擊
        attack_key = self.move_keys['attack']
        pyautogui.press(attack_key)
        
        # 嘗試使用技能
        for skill in ['skill1', 'skill2', 'skill3']:
            skill_key = self.move_keys.get(skill)
            if skill_key and self.use_skill(skill_key):
                break
        
        return True
    
    def combat_loop(self, duration: int = 60):
        """
        戰鬥循環
        :param duration: 持續時間(秒)
        """
        print(f"\n⚔️ 開始戰鬥模式 (持續 {duration} 秒)...")
        
        self.combat_mode = True
        start_time = time.time()
        
        while time.time() - start_time < duration and self.is_running:
            # 1. 檢查血量
            hp = self.detect_hp()
            if hp and hp < self.combat_config['hp_potion_threshold']:
                self.use_potion('hp')
                if self.callbacks['on_hp_low']:
                    self.callbacks['on_hp_low'](hp)
            
            # 2. 偵測敵人
            self.detect_enemies()
            
            # 3. 找到最近的敵人
            target = self.find_nearest_enemy()
            
            if target:
                # 4. 攻擊敵人
                self.attack_enemy(target)
                time.sleep(0.1)
            else:
                # 5. 沒有敵人,繼續探索
                char_pos = self.find_character_position()
                if char_pos:
                    terrain = self.map_data.get((char_pos.x, char_pos.y))
                    if terrain and terrain.can_walk_right:
                        self.move_direction('right', duration=0.5)
                    elif terrain and terrain.can_walk_left:
                        self.move_direction('left', duration=0.5)
                
                time.sleep(0.3)
        
        self.combat_mode = False
        print("✅ 戰鬥模式結束")
        
    def move_to_position(self, target: Position) -> bool:
        """
        移動到指定位置
        :param target: 目標位置
        :return: 是否成功開始移動
        """
        if not self.character_position:
            return False
        
        # 判斷方向
        dx = target.x - self.character_position.x
        dy = target.y - self.character_position.y
        
        # 水平移動
        if abs(dx) > 10:
            direction = 'right' if dx > 0 else 'left'
            self.move_direction(direction, duration=0.3)
        
        # 垂直移動
        if abs(dy) > 10:
            if dy < 0:  # 往上
                self.move_direction('jump', duration=0.2)
            else:  # 往下
                self.move_direction('down', duration=0.2)
        
        return True
    
    # ============================================
    # 數據持久化
    # ============================================
    
    # ============================================
    # 卡住偵測與脫困
    # ============================================
    
    def detect_stuck(self) -> bool:
        """
        偵測是否卡住
        :return: 是否卡住
        """
        if not self.safety_config['stuck_detection']:
            return False
        
        # 檢查最近的位置歷史
        if len(self.exploration_history) < 5:
            return False
        
        # 取最近5個位置
        recent = list(self.exploration_history)[-5:]
        
        # 計算位置變化
        max_distance = 0
        for i in range(len(recent)-1):
            for j in range(i+1, len(recent)):
                dist = recent[i].distance_to(recent[j])
                max_distance = max(max_distance, dist)
        
        # 如果5次移動的最大距離小於閾值,視為卡住
        if max_distance < self.config['position_similarity_threshold']:
            self.safety_config['stuck_counter'] += 1
            
            if self.safety_config['stuck_counter'] >= self.safety_config['stuck_threshold']:
                print("⚠️ 偵測到卡住!")
                self.stats['stuck_events'] += 1
                
                if self.callbacks['on_stuck']:
                    self.callbacks['on_stuck'](self.character_position)
                
                return True
        else:
            # 重置計數器
            self.safety_config['stuck_counter'] = 0
        
        return False
    
    def escape_stuck(self):
        """嘗試脫困"""
        print("🆘 嘗試脫困...")
        
        # 策略1: 隨機跳躍
        for _ in range(3):
            pyautogui.press(self.move_keys['jump'])
            time.sleep(0.2)
        
        # 策略2: 反方向移動
        self.move_direction('left', duration=0.5)
        time.sleep(0.2)
        self.move_direction('right', duration=0.5)
        time.sleep(0.2)
        
        # 策略3: 向下移動
        self.move_direction('down', duration=0.5)
        
        # 重置卡住計數器
        self.safety_config['stuck_counter'] = 0
        self.exploration_history.clear()
        
        print("✅ 脫困完成")
    
    # ============================================
    # 統計與報告
    # ============================================
    
    def update_stats(self):
        """更新統計數據"""
        if self.stats['start_time']:
            self.stats['exploration_time'] = time.time() - self.stats['start_time']
        
        self.stats['positions_explored'] = len(self.explored_positions)
        self.stats['enemies_found'] = len(self.enemies)
        
        if self.callbacks['on_stats_update']:
            self.callbacks['on_stats_update'](self.stats)
    
    def print_stats(self):
        """列印統計數據"""
        print("\n" + "="*50)
        print("📊 探索統計報告")
        print("="*50)
        
        elapsed = self.stats['exploration_time']
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        
        print(f"⏱️  總探索時間: {hours:02d}:{minutes:02d}:{seconds:02d}")
        print(f"🗺️  探索位置數: {self.stats['positions_explored']}")
        print(f"🎯 發現敵人數: {self.stats['enemies_found']}")
        print(f"⚔️  擊殺敵人數: {self.stats['enemies_killed']}")
        print(f"💀 死亡次數: {self.stats['deaths']}")
        print(f"🆘 卡住次數: {self.stats['stuck_events']}")
        
        if elapsed > 0:
            explore_rate = self.stats['positions_explored'] / (elapsed / 60)
            print(f"📈 探索效率: {explore_rate:.1f} 位置/分鐘")
        
        print("="*50 + "\n")
    
    def export_stats(self, filepath: str = "navigation_stats.json"):
        """匯出統計數據"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        print(f"📊 統計數據已匯出: {filepath}")
    
    # ============================================
    # 數據持久化
    # ============================================
    
    def save_map_data(self, filepath: str = "learned_map.json"):
        """儲存學習到的地圖數據"""
        data = {
            'explored_positions': [{'x': x, 'y': y} for x, y in self.explored_positions],
            'map_data': {
                f"{x},{y}": terrain.to_dict() 
                for (x, y), terrain in self.map_data.items()
            },
            'enemies': [enemy.to_dict() for enemy in self.enemies],
            'stats': self.stats,
            'config': self.config
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 地圖數據已儲存: {filepath}")
        self.print_stats()
    
    def load_map_data(self, filepath: str = "learned_map.json"):
        """載入地圖數據"""
        if not os.path.exists(filepath):
            print(f"⚠️ 找不到地圖檔案: {filepath}")
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 還原數據
        self.explored_positions = {(p['x'], p['y']) for p in data['explored_positions']}
        
        self.map_data = {}
        for key, terrain_dict in data['map_data'].items():
            x, y = map(int, key.split(','))
            terrain = TerrainInfo(**terrain_dict)
            self.map_data[(x, y)] = terrain
        
        print(f"📂 已載入地圖數據: {len(self.explored_positions)} 個位置")
    
    # ============================================
    # 控制接口
    # ============================================
    
    def start(self):
        """啟動系統"""
        self.is_running = True
        self.stats['start_time'] = time.time()
        print("🚀 自適應導航系統已啟動")
    
    def stop(self):
        """停止系統"""
        self.is_running = False
        print("⏹️ 自適應導航系統已停止")
        
        # 更新並顯示統計
        self.update_stats()
        self.print_stats()
        
        # 自動儲存
        self.save_map_data()
        self.export_stats()
    
    def set_callback(self, event: str, callback):
        """
        設定回調函數
        可用事件:
        - on_terrain_learned: 學習到新地形
        - on_enemy_detected: 偵測到敵人
        - on_position_updated: 位置更新
        - on_stuck: 卡住時
        - on_death: 死亡時
        - on_hp_low: 血量過低
        - on_stats_update: 統計更新
        """
        if event in self.callbacks:
            self.callbacks[event] = callback
        else:
            print(f"⚠️ 未知事件: {event}")
    
    def get_config(self) -> Dict:
        """取得當前配置"""
        return self.config.copy()
    
    def update_config(self, new_config: Dict):
        """
        更新配置
        :param new_config: 新配置字典
        """
        self.config.update(new_config)
        print("✅ 配置已更新")
    
    def set_priority_enemies(self, enemy_types: List[str]):
        """
        設定優先攻擊的敵人類型
        :param enemy_types: 敵人類型列表 (按優先級排序)
        """
        self.priority_enemies = enemy_types
        print(f"🎯 優先目標已設定: {', '.join(enemy_types)}")


# ============================================
# 使用範例
# ============================================

if __name__ == "__main__":
    # 創建系統
    nav = AdaptiveNavigationSystem()
    
    # 鎖定遊戲視窗
    nav.lock_game_window("MapleStory")  # 替換為實際遊戲視窗標題
    
    # 設定角色模板
    nav.set_character_template("images/character.png")
    
    # 添加敵人模板
    nav.add_enemy_template("A怪", "images/enemy_a.png")
    nav.add_enemy_template("B怪", "images/enemy_b.png")
    
    # 設定移動按鍵 (根據遊戲調整)
    nav.move_keys = {
        'left': 'left',
        'right': 'right',
        'up': 'up',
        'down': 'down',
        'jump': 'alt',
        'attack': 'ctrl'
    }
    
    # 設定回調
    def on_enemy_found(enemy):
        print(f"🎯 發現目標: {enemy.enemy_type} at {enemy.position.to_dict()}")
    
    nav.set_callback('on_enemy_detected', on_enemy_found)
    
    # 啟動並探索
    nav.start()
    nav.explore_surroundings(duration=60)  # 探索60秒
    nav.stop()
    
    print("\n📊 探索統計:")
    print(f"   探索位置: {len(nav.explored_positions)}")
    print(f"   發現敵人: {len(nav.enemies)}")
