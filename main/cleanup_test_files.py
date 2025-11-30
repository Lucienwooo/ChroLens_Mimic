#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動清理開發檔案工具
功能: 
1. 清理測試腳本 (test_*.py, quick_*.py，保留 test_editor_manual.py)
2. 清理臨時測試報告

使用方式:
    python cleanup_test_files.py
"""

import os
import sys

def cleanup_test_files():
    """清理測試檔案"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 要清理的測試檔案模式
    test_patterns = [
        "test_editor_save.py",
        "test_label_save.py", 
        "test_editor.py",
        "test_enhancements.py",
        "quick_test*.py",
        "run_test*.py",
        # 保留 test_editor_manual.py (手動測試工具)
    ]
    
    cleaned = []
    for pattern in test_patterns:
        if "*" in pattern:
            # 處理通配符
            prefix = pattern.replace("*.py", "")
            for filename in os.listdir(current_dir):
                if filename.startswith(prefix) and filename.endswith(".py"):
                    filepath = os.path.join(current_dir, filename)
                    try:
                        os.remove(filepath)
                        cleaned.append(filename)
                        print(f"✅ 已清理測試腳本: {filename}")
                    except Exception as e:
                        print(f"❌ 清理失敗 {filename}: {e}")
        else:
            # 精確匹配
            filepath = os.path.join(current_dir, pattern)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    cleaned.append(pattern)
                    print(f"✅ 已清理測試腳本: {pattern}")
                except Exception as e:
                    print(f"❌ 清理失敗 {pattern}: {e}")
    
    if cleaned:
        print(f"\n🗑️ 測試檔案: 總計清理 {len(cleaned)} 個")
    else:
        print("ℹ️ 沒有需要清理的測試檔案")

def show_remaining_docs():
    """顯示保留的文檔"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    md_files = [f for f in os.listdir(current_dir) if f.endswith('.md')]
    
    if md_files:
        print(f"\n📚 保留的文檔 ({len(md_files)} 個):")
        important_docs = {
            "README.md": "專案主要說明",
            "CHANGELOG.md": "開發變更日誌",
            "指令說明.md": "文字指令手冊",
            "標籤使用範例.md": "標籤語法範例",
            "重構計畫.md": "重構規劃",
            "重構完成報告.md": "重構記錄",
            "修復說明_編輯器問題.md": "編輯器修復",
            "強化與整理完成報告.md": "圖片辨識強化"
        }
        
        for f in sorted(md_files):
            desc = important_docs.get(f, "")
            if desc:
                print(f"   - {f:<30} {desc}")
            else:
                print(f"   - {f}")

if __name__ == "__main__":
    print("=" * 60)
    print("ChroLens Mimic - 開發檔案清理工具")
    print("=" * 60)
    
    cleanup_test_files()
    show_remaining_docs()
    
    print("\n" + "=" * 60)
    print("✅ 清理完成!")
    print("=" * 60)

