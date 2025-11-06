@echo off
REM 一鍵打包工具 - 自動處理檔案鎖定問題

cd /d "%~dp0"

echo.
echo ==========================================
echo ChroLens_Mimic 一鍵打包工具
echo ==========================================
echo.

REM 步驟1: 關閉可能佔用檔案的程序
echo [步驟 1/4] 關閉相關程序...
taskkill /F /IM ChroLens_Mimic.exe >nul 2>&1
timeout /t 1 /nobreak >nul

REM 步驟2: 清理舊檔案
echo [步驟 2/4] 清理舊檔案...
if exist dist rmdir /s /q dist >nul 2>&1
if exist build rmdir /s /q build >nul 2>&1
timeout /t 1 /nobreak >nul

REM 如果還是無法刪除，重啟 Explorer
if exist dist (
    echo [提示] 檔案被鎖定，重啟檔案總管...
    taskkill /F /IM explorer.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    rmdir /s /q dist >nul 2>&1
    rmdir /s /q build >nul 2>&1
    start explorer.exe
    timeout /t 2 /nobreak >nul
)

REM 步驟3: 執行打包
echo [步驟 3/4] 執行打包...
python build_simple.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [錯誤] 打包失敗！
    echo.
    echo 請嘗試以下步驟：
    echo 1. 手動刪除 dist 和 build 資料夾
    echo 2. 重新執行此腳本
    echo.
    pause
    exit /b 1
)

REM 步驟4: 顯示結果
echo [步驟 4/4] 檢查結果...
if exist "dist\ChroLens_Mimic\ChroLens_Mimic.exe" (
    echo.
    echo ==========================================
    echo 打包成功！
    echo ==========================================
    echo.
    echo 輸出位置:
    echo   EXE: dist\ChroLens_Mimic\ChroLens_Mimic.exe
    if exist "dist\ChroLens_Mimic.zip" (
        echo   ZIP: dist\ChroLens_Mimic.zip
    )
    echo.
) else (
    echo.
    echo [錯誤] 找不到生成的 EXE 檔案！
    echo.
)

pause
