ChroLens_Mimic - 簡易測試與 SOP（長時間／重複測試）

前置作業
1. 安裝 Python 3.8+（推薦使用官方安裝程式）
   - 下載：https://www.python.org/downloads/
   - 務必勾選『Add Python to PATH』或手動把 Python 安裝路徑加入系統 PATH

2. 開啟 PowerShell（以使用者或系統管理員視窗皆可，但鍵盤 hook 需要管理員）

3. 在專案資料夾（包含 main 資料夾）安裝依賴：
```powershell
# 進入專案根目錄
cd C:\Users\Lucien\Documents\GitHub\ChroLens_Mimic
# 建議先升級 pip
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt
```

快速啟動（開發環境）
- 執行 GUI 應用程式（若要直接啟動）：
```powershell
py -3 main\ChroLens_Mimic.py
```
- 注意：`keyboard` 模組需要管理員權限才能正常做全局 hotkey。若熱鍵無效，請以「以系統管理員身份執行 PowerShell/命令提示字元」再啟動應用。

測試重複/重複時間/隨機時間功能（不啟動 GUI）
- 我提供了一個獨立模擬測試程式，不會啟動 GUI，方便在沒有完整依賴或在非管理員情況下驗證排程/重複邏輯：
```powershell
# 範例 1：重複 3 次，間隔 30 秒
py -3 main\tests\test_repeat_sim.py --repeat 3 --interval 00:00:30

# 範例 2：無限重複（直到手動停止）
py -3 main\tests\test_repeat_sim.py --repeat 0 --interval 00:00:10

# 範例 3：重複 5 次，基礎間隔 10 秒，啟用隨機化（每次等待 0..10秒）
py -3 main\tests\test_repeat_sim.py --repeat 5 --interval 00:00:10 --random

# 範例 4：設定總運作時間為 1 小時（無視 repeat 次數，遇到時間上限則停止）
py -3 main\tests\test_repeat_sim.py --repeat 0 --repeat_time 01:00:00 --interval 00:00:05
```

如何執行長時間負載測試（建議）
1. 在保證系統穩定與可監控的情況下，先在非生產機或 VM 執行。
2. 可結合 Windows 任務排程或簡單 loop 執行 GUI 或錄製腳本，並同時監控任務管理員（記憶體、CPU、Handle 數量）。

建議的壓力測試腳本（範例流程）
- 用 test_repeat_sim.py 模擬「極短間隔 + 大量次數」來模擬高頻處理：
```powershell
py -3 main\tests\test_repeat_sim.py --repeat 10000 --interval 00:00:00 --event_duration 0
```
- 若要真實測試 GUI 的長時間運作（會與系統 hook 與 I/O 有關），請以管理員執行 GUI，然後讓它持續跑同一腳本數小時，觀察是否有記憶體增加、熱鍵遺失、或按鍵卡住等問題。

常見情境模擬（使用者範例）
- 想要重複 3 次：在 GUI 中把「重複次數」填 3。
- 想要無限重複：在 GUI 中把「重複次數」填 0（0 表示無限）。
- 想要總共運作 1.5 小時：把「重複時間」填 01:30:00，並把重複次數填 0 或大數值。
- 想要每次之間隨機等待：勾選「隨機」選項，並在「重複間隔」填入最大間隔（程式會在 0..該值之間隨機）。

故障排除小提示
- 若熱鍵在執行一段時間後失效：確認是否有其他程式佔用全局 hook，或是否程式崩潰了某個監聽 thread。可嘗試按預設的 force_quit 快捷鍵 (預設 ctrl+alt+end) 強制結束並重啟。
- 若發生「按鍵卡住」情況：關閉程式後使用鍵盤實體按一次被卡住的鍵或重啟系統；後續我已在 recorder 中新增 pressed-key 追蹤與釋放機制以減少此問題。

後續（可選）
- 若需要，我可以幫你：
  - 建立自動化測試套件（pytest）來覆蓋多種情境
  - 建立長時間監控腳本（記憶體/handle/log rotate）並自動截取快照
  - 協助把整個應用打包成可攜式 .exe

---
如果你要我幫你在本機執行這些測試，請先在你的電腦上安裝 Python（並在此回報安裝結果），或允許我指導你逐步操作。