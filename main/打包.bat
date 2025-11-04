@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ========================================
echo ChroLens_Mimic 快速打包工具
echo ========================================
echo.

REM 檢查 Python 是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 找不到 Python
    echo 請先安裝 Python 3.8 或更新版本
    echo.
    pause
    exit /b 1
)

echo [✓] Python 已安裝
echo.

REM 檢查 build.py 是否存在
if not exist "build.py" (
    echo [錯誤] 找不到 build.py
    echo 請在 main 目錄中執行此腳本
    echo.
    pause
    exit /b 1
)

echo [✓] 找到 build.py
echo.
echo 開始打包...
echo.

REM 執行 build.py
python build.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo [✗] 打包失敗！
    echo ========================================
    echo.
    echo 請檢查錯誤訊息並重試
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo [✓] 打包成功！
echo ========================================
echo.
echo 輸出目錄: dist\ChroLens_Mimic
echo 主程式: dist\ChroLens_Mimic\ChroLens_Mimic.exe
echo.

REM 詢問是否開啟目錄
set /p openDir="是否開啟輸出目錄? (Y/N): "
if /i "%openDir%"=="Y" (
    start "" "dist\ChroLens_Mimic"
)

echo.
pause
