# 🎮 ChroLens 自適應導航系統

一個透過**實際移動測試**來學習 2D 橫向卷軸遊戲地圖的智能導航系統。

## ✨ 核心特色

### 🧠 自主學習
- **不需要預先知識** - 透過實際按鍵測試來了解環境
- **自動建立地圖** - 記錄可行的移動路徑
- **智能探索** - 優先探索未知區域
- **持久化學習** - 儲存並重用地圖知識

### ⚔️ 自動戰鬥
- **敵人偵測** - 自動識別並追蹤敵人
- **智能攻擊** - 自動移動並攻擊目標
- **技能輪替** - 自動使用技能(含冷卻管理)
- **藥水管理** - 血量過低自動補血

### 🛡️ 安全機制
- **卡住偵測** - 自動識別卡住狀態
- **自動脫困** - 嘗試多種策略脫困
- **血量監控** - 即時偵測血量並預警
- **統計追蹤** - 詳細記錄探索數據

## 📦 安裝要求

```bash
pip install opencv-python numpy pyautogui pywin32
```

已包含的依賴(ChroLens_Mimic):
- `image_recognition.py` - 圖片識別模組

## 🚀 快速開始

### 方法 1: 最簡單 (推薦新手)

```python
from adaptive_navigation_system import AdaptiveNavigationSystem

# 創建系統
nav = AdaptiveNavigationSystem()

# 鎖定遊戲視窗
nav.lock_game_window("楓之谷")  # 替換為你的遊戲視窗標題

# 設定角色圖片
nav.set_character_template("images/my_character.png")

# 添加敵人圖片
nav.add_enemy_template("蝸牛", "images/snail.png")

# 一鍵啟動!
nav.start()
nav.explore_surroundings(duration=300, auto_combat=True)  # 5分鐘
nav.stop()
```

### 方法 2: 使用配置檔案 (推薦進階)

1. **生成配置模板**
```bash
python navigation_config_loader.py template
```

2. **編輯配置檔案** (`navigation_config.json`)
```json
{
  "遊戲設定": {
    "window_title": "你的遊戲"
  },
  "識別設定": {
    "character_template": "images/char.png",
    "enemy_templates": {
      "怪物A": "images/enemy_a.png"
    }
  },
  "按鍵設定": {
    "move_keys": {
      "left": "left",
      "right": "right",
      "jump": "alt",
      "attack": "ctrl"
    }
  }
}
```

3. **啟動系統**
```bash
python navigation_config_loader.py start navigation_config.json 300
```

或在程式中:
```python
from navigation_config_loader import quick_start_from_config

quick_start_from_config("navigation_config.json", duration=300, auto_combat=True)
```

### 方法 3: 查看完整範例

```bash
python adaptive_navigation_example.py
```

## 📋 使用步驟

### 1️⃣ 準備素材

**角色圖片** (`images/character.png`)
- 截取你的角色清晰圖片
- 建議大小: 40x40 到 80x80 像素
- 確保背景對比清晰

**敵人圖片** (`images/enemy_*.png`)
- 為每種要打的怪物截圖
- 同樣要求清晰、對比明顯

**截圖技巧**:
```python
# 使用內建工具截圖
import pyautogui
pyautogui.screenshot("images/screenshot.png", region=(x, y, width, height))
```

### 2️⃣ 配置系統

```python
nav = AdaptiveNavigationSystem()

# 設定遊戲按鍵
nav.move_keys = {
    'left': 'left',
    'right': 'right',
    'up': 'up',
    'down': 'down',
    'jump': 'alt',      # 你的跳躍鍵
    'attack': 'ctrl',   # 你的攻擊鍵
    'skill1': 'a',      # 技能1
    'skill2': 's',      # 技能2
    'hp_potion': 'pageup'  # 補血鍵
}

# 設定技能冷卻時間
nav.combat_config['skill_cooldowns'] = {
    'a': 5.0,   # 技能1冷卻5秒
    's': 8.0    # 技能2冷卻8秒
}

# 設定血量閾值
nav.combat_config['hp_potion_threshold'] = 0.5  # 50%以下喝水
```

### 3️⃣ 執行探索

```python
# 啟動系統
nav.start()

# 探索 + 自動戰鬥
nav.explore_surroundings(
    duration=300,      # 探索5分鐘
    auto_combat=True   # 啟用自動戰鬥
)

# 停止並儲存
nav.stop()  # 自動儲存地圖到 learned_map.json
```

### 4️⃣ 重用學習成果

```python
# 下次直接載入之前的地圖
nav.load_map_data("learned_map.json")

# 繼續探索(會利用已知地圖)
nav.start()
nav.explore_surroundings(duration=180)
nav.stop()
```

## ⚙️ 進階配置

### 調整識別參數

```python
# 提高識別精確度(更嚴格)
nav.config['recognition_confidence'] = 0.85

# 縮短移動測試時間(更快但可能不準)
nav.config['move_test_duration'] = 0.2

# 調整畫面變化閾值
nav.config['movement_threshold'] = 15
```

### 設定回調函數

```python
# 發現敵人時觸發
def on_enemy_found(enemy):
    print(f"🎯 發現 {enemy.enemy_type}!")

nav.set_callback('on_enemy_detected', on_enemy_found)

# 血量過低時觸發
def on_hp_low(hp):
    print(f"⚠️ 血量: {hp*100:.0f}%")
    # 可以在這裡做額外處理,如逃跑

nav.set_callback('on_hp_low', on_hp_low)

# 卡住時觸發
def on_stuck(position):
    print(f"🆘 卡住了! 位置: {position}")

nav.set_callback('on_stuck', on_stuck)
```

### 自訂控制流程

```python
nav.start()

for i in range(10):
    # 1. 定位角色
    pos = nav.find_character_position()
    
    # 2. 學習地形
    terrain = nav.learn_current_terrain()
    
    # 3. 偵測敵人
    enemies = nav.detect_enemies()
    
    # 4. 攻擊敵人
    if enemies:
        target = nav.find_nearest_enemy()
        nav.attack_enemy(target)
    
    # 5. 移動
    if terrain.can_walk_right:
        nav.move_direction('right', duration=1.0)

nav.stop()
```

## 📊 統計數據

系統會自動追蹤以下數據:

```python
nav.stats = {
    'exploration_time': 0,      # 總探索時間
    'positions_explored': 0,    # 探索位置數
    'enemies_found': 0,         # 發現敵人數
    'enemies_killed': 0,        # 擊殺數
    'deaths': 0,                # 死亡次數
    'stuck_events': 0           # 卡住次數
}

# 顯示統計
nav.print_stats()

# 匯出統計
nav.export_stats("stats.json")
```

## 🔍 除錯技巧

### 測試視窗鎖定

```python
nav = AdaptiveNavigationSystem()
success = nav.lock_game_window("遊戲名稱")
print(f"視窗鎖定: {'成功' if success else '失敗'}")
print(f"視窗位置: {nav.game_rect}")
```

### 測試角色識別

```python
nav.set_character_template("images/char.png")
pos = nav.find_character_position()
if pos:
    print(f"✅ 找到角色: ({pos.x}, {pos.y})")
else:
    print("❌ 找不到角色,請檢查模板圖片")
```

### 測試移動

```python
# 測試各方向移動
for direction in ['left', 'right', 'jump', 'up', 'down']:
    result = nav.test_movement(direction)
    print(f"{direction}: {'✅' if result else '❌'}")
```

### 查看截圖

```python
screenshot = nav.capture_game_screen()
if screenshot is not None:
    cv2.imshow("Game Screen", screenshot)
    cv2.waitKey(0)
```

## 🎯 最佳實踐

### 1. 圖片素材建議
- ✅ 使用清晰、對比強的圖片
- ✅ 角色圖片包含獨特特徵
- ✅ 敵人圖片要有代表性
- ❌ 避免模糊或太小的圖片
- ❌ 避免包含太多背景

### 2. 參數調整建議
- **識別信心度**: 0.7-0.8 (平衡速度與準確度)
- **移動測試時長**: 0.2-0.4秒 (根據遊戲速度調整)
- **畫面變化閾值**: 8-15 (根據畫面複雜度調整)

### 3. 安全使用建議
- ✅ 先在安全地圖測試
- ✅ 設定合理的探索時長
- ✅ 啟用卡住偵測
- ✅ 設定血量閾值
- ❌ 不要在重要任務時使用
- ❌ 不要長時間無人監控

### 4. 效能優化
```python
# 啟用截圖快取
nav.config['cache_screenshots'] = True

# 調整截圖間隔
nav.config['screenshot_interval'] = 0.15

# 降低識別頻率(在探索函數中增加 sleep)
```

## 📝 常見問題

**Q: 找不到角色/敵人?**
- 檢查模板圖片是否清晰
- 降低 `recognition_confidence`
- 啟用 `multi_scale_search`

**Q: 移動測試總是失敗?**
- 增加 `move_test_duration`
- 降低 `movement_threshold`
- 確認按鍵設定正確

**Q: 角色一直卡住?**
- 降低 `stuck_threshold`
- 檢查地形學習是否準確
- 手動測試移動是否正常

**Q: 自動戰鬥不攻擊?**
- 檢查敵人模板是否正確
- 調整 `attack_range`
- 確認攻擊鍵設定正確

## 🔧 系統架構

```
adaptive_navigation_system.py     # 核心系統
├─ Position                       # 位置數據類
├─ TerrainInfo                    # 地形資訊類
├─ EnemyInfo                      # 敵人資訊類
└─ AdaptiveNavigationSystem       # 主系統類
   ├─ 視窗管理
   │  ├─ lock_game_window()      # 鎖定視窗
   │  └─ capture_game_screen()   # 截圖
   ├─ 角色定位
   │  └─ find_character_position() # 找角色
   ├─ 移動學習
   │  ├─ test_movement()          # 測試移動
   │  └─ learn_current_terrain()  # 學習地形
   ├─ 探索系統
   │  └─ explore_surroundings()   # 自動探索
   ├─ 敵人偵測
   │  ├─ detect_enemies()         # 偵測敵人
   │  └─ find_nearest_enemy()     # 找最近敵人
   ├─ 戰鬥系統
   │  ├─ attack_enemy()           # 攻擊敵人
   │  ├─ use_skill()              # 使用技能
   │  └─ combat_loop()            # 戰鬥循環
   ├─ 安全機制
   │  ├─ detect_stuck()           # 偵測卡住
   │  └─ escape_stuck()           # 脫困
   └─ 數據管理
      ├─ save_map_data()          # 儲存地圖
      └─ load_map_data()          # 載入地圖
```

## 📚 相關檔案

- `adaptive_navigation_system.py` - 核心系統
- `adaptive_navigation_example.py` - 使用範例集合
- `navigation_config_loader.py` - 配置載入工具
- `navigation_config.json` - 配置檔案模板

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request!

## 📄 授權

MIT License

## 👨‍💻 作者

ChroLens Team

---

**⚠️ 免責聲明**: 此工具僅供學習研究使用。使用自動化工具可能違反某些遊戲的服務條款,請自行承擔風險。
