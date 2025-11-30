"""
專案檔案清理工具
清理測試檔案、建置檔案和其他不必要的檔案
"""

import os
import shutil
from pathlib import Path

def clean_project():
    """清理專案中的多餘檔案"""
    project_dir = Path(__file__).parent
    main_dir = project_dir / "main"
    
    print("🧹 開始清理專案檔案...\n")
    
    # 統計
    deleted_count = 0
    
    # 1. 清理建置目錄
    print("📁 清理建置目錄...")
    build_dirs = [
        main_dir / "build",
        main_dir / "dist",
        main_dir / "__pycache__",
    ]
    
    for dir_path in build_dirs:
        if dir_path.exists():
            print(f"  ✓ 刪除: {dir_path.relative_to(project_dir)}/")
            shutil.rmtree(dir_path, ignore_errors=True)
            deleted_count += 1
    
    # 2. 清理 spec 檔案
    print("\n📄 清理 spec 檔案...")
    for spec_file in main_dir.glob("*.spec"):
        print(f"  ✓ 刪除: {spec_file.name}")
        spec_file.unlink()
        deleted_count += 1
    
    # 3. 清理測試檔案
    print("\n🧪 清理測試檔案...")
    test_patterns = [
        "test_*.py",
        "*_test.py",
        "quick_*.py",
        "run_*.py"
    ]
    
    # 保留的測試檔案
    keep_files = ["test_editor_manual.py"]
    
    for pattern in test_patterns:
        for test_file in main_dir.glob(pattern):
            if test_file.name not in keep_files:
                print(f"  ✓ 刪除: {test_file.name}")
                test_file.unlink()
                deleted_count += 1
    
    # 4. 清理重複的說明檔案
    print("\n📝 清理重複的說明檔案...")
    
    # 檢查是否有 指令說明.html（主要版本）
    if (main_dir / "指令說明.html").exists():
        # 刪除舊的 markdown 版本
        redundant_docs = [
            main_dir / "ChroLens_文字指令完整指南.md",
            main_dir / "指令說明.md"  # 如果與 HTML 重複
        ]
        
        for doc_file in redundant_docs:
            if doc_file.exists():
                # 先確認內容是否與 HTML 重複
                print(f"  ⚠️  發現: {doc_file.name}")
                response = input(f"    是否刪除？(y/N): ")
                if response.lower() == 'y':
                    print(f"  ✓ 刪除: {doc_file.name}")
                    doc_file.unlink()
                    deleted_count += 1
                else:
                    print(f"  ⊘ 保留: {doc_file.name}")
    
    # 5. 清理臨時檔案
    print("\n🗑️  清理臨時檔案...")
    temp_patterns = [
        "*.pyc",
        "*.pyo",
        "*.tmp",
        ".DS_Store",
        "Thumbs.db"
    ]
    
    for pattern in temp_patterns:
        for temp_file in main_dir.rglob(pattern):
            print(f"  ✓ 刪除: {temp_file.relative_to(project_dir)}")
            temp_file.unlink()
            deleted_count += 1
    
    # 6. 清理空目錄
    print("\n📂 清理空目錄...")
    for root, dirs, files in os.walk(main_dir, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            if dir_path.exists() and not any(dir_path.iterdir()):
                if dir_name not in ["images", "scripts", "modules", "TTF"]:  # 保留必要的空目錄
                    print(f"  ✓ 刪除空目錄: {dir_path.relative_to(project_dir)}/")
                    dir_path.rmdir()
                    deleted_count += 1
    
    # 完成
    print(f"\n{'='*60}")
    print(f"✅ 清理完成！共刪除 {deleted_count} 個項目")
    print(f"{'='*60}\n")
    
    # 顯示保留的重要檔案
    print("📋 保留的重要檔案：")
    important_files = [
        "ChroLens_Mimic.py",
        "text_script_editor.py",
        "visual_script_editor.py",
        "recorder.py",
        "script_io.py",
        "lang.py",
        "指令說明.html",
        "更新說明_v*.md",
        "auto_release.py",
        "build_simple.py"
    ]
    
    for pattern in important_files:
        if "*" in pattern:
            files = list(main_dir.glob(pattern))
            for f in files:
                print(f"  ✓ {f.name}")
        else:
            if (main_dir / pattern).exists():
                print(f"  ✓ {pattern}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ChroLens_Mimic 專案清理工具")
    print("="*60 + "\n")
    
    print("此工具將刪除以下檔案：")
    print("  • build/、dist/、__pycache__/ 目錄")
    print("  • *.spec 檔案")
    print("  • test_*.py、*_test.py、quick_*.py、run_*.py")
    print("  • 臨時檔案（*.pyc、*.pyo、*.tmp）")
    print("  • 重複的說明文件（需確認）")
    print()
    
    response = input("是否繼續？(y/N): ")
    if response.lower() != 'y':
        print("已取消")
    else:
        clean_project()
