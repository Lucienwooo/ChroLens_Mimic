@echo off
chcp 65001 > nul
echo ========================================
echo ChroLens_Mimic 快速打包工具
echo ========================================
echo.

cd /d "%~dp0"

echo [提示] 請確保所有 dist 目錄中的檔案都已關閉
echo.
timeout /t 3 /nobreak >nul

echo [1/3] 嘗試清理舊檔案...
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul
echo.

echo [2/3] 開始打包...
python build_simple.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 打包失敗！
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ 打包完成！
echo ========================================
echo.
echo 輸出位置:
echo   - EXE: dist\ChroLens_Mimic\
echo   - ZIP: dist\ChroLens_Mimic.zip
echo.
echo [3/3] 檢視結構...
cd dist\ChroLens_Mimic
dir /b
echo.

pause
