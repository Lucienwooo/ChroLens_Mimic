"""
快捷鍵穩定性測試腳本
測試目標：確認 F10/F9 可以連續使用 5 次以上而不失效
"""
import time
print("=" * 60)
print("快捷鍵穩定性測試")
print("=" * 60)
print("\n請按照以下步驟測試：\n")
print("1. 以管理員身份啟動 ChroLens_Mimic.exe")
print("2. 執行以下測試循環 5 次：")
print("   a) 按 F10 開始錄製")
print("   b) 等待 2-3 秒")
print("   c) 按 F9 停止錄製")
print("   d) 檢查腳本是否正常儲存")
print("\n3. 記錄結果：")
print("   ✓ 成功：F9 立即停止並儲存腳本")
print("   ✗ 失敗：F9 無反應，需手動點擊停止按鈕")
print("\n4. 測試標準：")
print("   - 應該能夠連續成功 5 次")
print("   - 每次 F9 都應立即響應")
print("   - 不應出現快捷鍵失效")
print("\n=" * 60)
print("開始測試...\n")

test_results = []
for i in range(5):
    input(f"\n第 {i+1} 次測試 - 按 Enter 繼續...")
    print(f"  1. 按 F10 開始錄製")
    time.sleep(1)
    print(f"  2. 等待 2-3 秒...")
    time.sleep(1)
    print(f"  3. 按 F9 停止錄製")
    result = input(f"  4. F9 是否正常停止？(y/n): ")
    test_results.append(result.lower() == 'y')
    
print("\n" + "=" * 60)
print("測試結果總結")
print("=" * 60)
success_count = sum(test_results)
print(f"\n成功次數：{success_count}/5")
print(f"成功率：{success_count/5*100:.0f}%")

for i, result in enumerate(test_results, 1):
    status = "✓" if result else "✗"
    print(f"  第 {i} 次：{status}")

if success_count == 5:
    print("\n🎉 測試通過！快捷鍵穩定性良好。")
else:
    print(f"\n⚠️ 測試失敗！有 {5-success_count} 次快捷鍵失效。")

print("\n=" * 60)
input("\n按 Enter 結束...")
