@echo off
chcp 65001 >nul
title ChroLens_Mimic 打包工具 v2.6.7
color 0A

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo    ChroLens_Mimic 自動打包工具
echo ═══════════════════════════════════════════════════════════════════════════
echo.

echo [1/3] 檢查環境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 錯誤：找不到 Python！請確認 Python 已安裝並加入 PATH
    pause
    exit /b 1
)

echo [2/3] 執行打包腳本...
echo.
python pack_safe.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ 打包失敗！請檢查錯誤訊息
    pause
    exit /b 1
)

echo.
echo [3/3] 打包完成！
echo.
echo ✅ 成功創建：dist\ChroLens_Mimic\
echo ✅ 壓縮檔案：ChroLens_Mimic_[版本號].zip
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo    打包完成！按任意鍵退出...
echo ═══════════════════════════════════════════════════════════════════════════
pause >nul
