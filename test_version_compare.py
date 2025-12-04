"""測試版本比較邏輯"""

def _compare_versions(current: str, latest: str) -> bool:
    """
    比較版本號
    
    Args:
        current: 當前版本（如 "2.6.3"）
        latest: 最新版本（如 "2.6.4"）
    
    Returns:
        如果 latest > current 返回 True
    """
    try:
        current_parts = [int(x) for x in current.split('.')]
        latest_parts = [int(x) for x in latest.split('.')]
        
        # 補齊長度
        max_len = max(len(current_parts), len(latest_parts))
        current_parts += [0] * (max_len - len(current_parts))
        latest_parts += [0] * (max_len - len(latest_parts))
        
        return latest_parts > current_parts
    except Exception as e:
        print(f"錯誤: {e}")
        return False

# 測試用例
test_cases = [
    ("2.6.6", "2.7.0", True, "2.6.6 -> 2.7.0"),
    ("2.6.7", "2.7.0", True, "2.6.7 -> 2.7.0"),
    ("2.7.0", "2.7.1", True, "2.7.0 -> 2.7.1"),
    ("2.6.6", "2.7.1", True, "2.6.6 -> 2.7.1"),
    ("2.6.7", "2.7.1", True, "2.6.7 -> 2.7.1"),
    ("2.7.1", "2.7.1", False, "2.7.1 -> 2.7.1 (相同)"),
    ("2.7.1", "2.7.0", False, "2.7.1 -> 2.7.0 (降級)"),
]

print("版本比較測試：\n")
all_pass = True
for current, latest, expected, desc in test_cases:
    result = _compare_versions(current, latest)
    status = "✅" if result == expected else "❌"
    if result != expected:
        all_pass = False
    print(f"{status} {desc}: {result} (期望: {expected})")

print(f"\n{'='*50}")
print(f"測試結果: {'全部通過 ✅' if all_pass else '有失敗 ❌'}")
