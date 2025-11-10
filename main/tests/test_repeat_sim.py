"""
簡單的重複 / 重複時間 / 隨機時間 模擬測試
此程式不會啟動 GUI，只模擬 ChroLens_Mimic 中使用的重複邏輯（重複次數、重複總時間、每次間隔與隨機化）
用意：在無 GUI 或未安裝整套依賴時，也能驗證 scheduling 與重複行為是否合理。

使用方式 (PowerShell):
  py -3 main\tests\test_repeat_sim.py --repeat 3 --interval 00:00:30 --repeat_time 00:10:00
  py -3 main\tests\test_repeat_sim.py --repeat 0   # 0 表示無限
  py -3 main\tests\test_repeat_sim.py --repeat 5 --interval 00:00:10 --random

輸出會顯示每次執行的預計啟動時間與已執行次數。
"""

import argparse
import random
import time
from datetime import datetime, timedelta


def parse_time_to_seconds(s: str) -> int:
    s = s.strip()
    if not s:
        return 0
    parts = s.split(":")
    try:
        parts = [int(p) for p in parts]
    except ValueError:
        raise ValueError("時間格式錯誤，請使用 HH:MM:SS 或 MM:SS 或 SS")
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError("時間格式錯誤")


def simulate_repeat(repeat_count: int, repeat_time_s: int, interval_s: int, randomize: bool, event_duration_s: int = 1, max_events: int = 10000):
    """
    repeat_count: 0 表示無限
    repeat_time_s: 總運作時間 (0 表示不限)
    interval_s: 每次重複之間等待的基礎秒數
    randomize: 若 True, 每次等待會在 0..interval_s 之間隨機
    event_duration_s: 每次事件模擬所耗秒數（預設 1 秒）
    max_events: safety cap
    """
    start = datetime.now()
    executed = 0
    iteration = 0
    next_start = start
    end_time = None
    if repeat_time_s > 0:
        end_time = start + timedelta(seconds=repeat_time_s)

    print(f"模擬開始: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    if repeat_count == 0:
        print("重複次數: 無限 (0 表示無限)")
    else:
        print(f"重複次數: {repeat_count}")
    if repeat_time_s > 0:
        print(f"總運作時間上限: {timedelta(seconds=repeat_time_s)}")
    print(f"每次間隔基礎: {interval_s}s, 隨機化: {randomize}")
    print("--- 模擬事件清單 (只列出時間與索引) ---")

    while True:
        now = datetime.now()
        if now < next_start:
            # wait until next_start (fast-forward simulation: we won't sleep long; for real test you can uncomment sleep)
            delta = (next_start - now).total_seconds()
            # For a quick deterministic simulation, advance time without sleeping.
            # time.sleep(min(delta, 0.01))
            now = next_start

        iteration += 1
        executed += 1
        print(f"[{executed}] 執行時間: {now.strftime('%H:%M:%S')} (iteration={iteration})")

        # 模擬事件執行時間
        # time.sleep(event_duration_s)  # 在快速模擬中我們不實際 sleep

        # decide next interval
        base_next = interval_s
        if randomize and interval_s > 0:
            wait = random.uniform(0, interval_s)
        else:
            wait = base_next

        next_start = now + timedelta(seconds=event_duration_s + wait)

        # Stop conditions
        if repeat_count > 0 and executed >= repeat_count:
            print("達到設定的重複次數，結束模擬。")
            break
        if end_time and next_start >= end_time:
            print("達到總運作時間上限，結束模擬。")
            break
        if executed >= max_events:
            print("達到安全上限，結束模擬。")
            break

    finish = datetime.now()
    elapsed = finish - start
    print("--- 模擬結束 ---")
    print(f"執行次數: {executed}, 總耗時(模擬): {elapsed}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repeat', type=int, default=1, help='重複次數 (0 表示無限)')
    parser.add_argument('--interval', type=str, default='00:00:01', help='每次間隔，格式 HH:MM:SS 或 MM:SS 或 SS')
    parser.add_argument('--repeat_time', type=str, default='00:00:00', help='總運作時間上限，格式 HH:MM:SS，0 表示不限')
    parser.add_argument('--random', action='store_true', help='啟用隨機化間隔 (在 0..interval 之間)')
    parser.add_argument('--event_duration', type=int, default=1, help='每次事件耗時（秒），僅供模擬）')
    parser.add_argument('--max_events', type=int, default=10000, help='安全上限')
    args = parser.parse_args()

    interval_s = parse_time_to_seconds(args.interval)
    repeat_time_s = parse_time_to_seconds(args.repeat_time)

    simulate_repeat(args.repeat, repeat_time_s, interval_s, args.random, event_duration_s=args.event_duration, max_events=args.max_events)
