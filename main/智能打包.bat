@echo off
chcp 65001 > nul
echo ========================================
echo ChroLens_Mimic 智能打包工具
echo ========================================
echo.

cd /d "%~dp0"

echo [檢查] 正在檢查是否有程序佔用檔案...
tasklist | findstr /I "ChroLens_Mimic.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo [警告] 發現 ChroLens_Mimic.exe 正在運行
    echo [動作] 正在關閉程序...
    taskkill /F /IM ChroLens_Mimic.exe 2>nul
    timeout /t 2 /nobreak >nul
)

echo [準備] 等待檔案系統釋放...
timeout /t 2 /nobreak >nul

echo.
echo [1/4] 強制清理舊檔案...
echo [提示] 如果遇到錯誤，請確保：
echo   1. 關閉檔案總管中的 dist 目錄
echo   2. 關閉任何打開的 ChroLens_Mimic.exe
echo   3. 等待 3 秒後自動繼續...
timeout /t 3 /nobreak >nul

REM 多次嘗試刪除
for /L %%i in (1,1,3) do (
    if exist dist (
        echo [嘗試 %%i/3] 刪除 dist...
        rmdir /s /q dist 2>nul
        timeout /t 1 /nobreak >nul
    )
)

for /L %%i in (1,1,3) do (
    if exist build (
        echo [嘗試 %%i/3] 刪除 build...
        rmdir /s /q build 2>nul
        timeout /t 1 /nobreak >nul
    )
)

if exist dist (
    echo [警告] 無法完全刪除 dist 目錄
    echo [提示] 將嘗試繼續打包...
)

echo.
echo [2/4] 開始打包程序...
python build_simple.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo ❌ 打包失敗！
    echo ========================================
    echo.
    echo [解決方案]
    echo 1. 完全關閉檔案總管
    echo 2. 執行以下命令：
    echo    taskkill /F /IM explorer.exe
    echo    start explorer.exe
    echo 3. 重新執行此腳本
    echo.
    pause
    exit /b 1
)

echo.
echo [3/4] 檢查打包結果...
if not exist "dist\ChroLens_Mimic\ChroLens_Mimic.exe" (
    echo ❌ 找不到主程式！
    pause
    exit /b 1
)

echo ✅ 主程式: dist\ChroLens_Mimic\ChroLens_Mimic.exe
if exist "dist\ChroLens_Mimic.zip" (
    echo ✅ ZIP 包: dist\ChroLens_Mimic.zip
)

echo.
echo [4/4] 顯示目錄結構...
cd dist\ChroLens_Mimic 2>nul && (
    echo.
    echo 📂 dist\ChroLens_Mimic\
    dir /b /a-d 2>nul
    echo.
    echo 📁 子目錄:
    dir /b /ad 2>nul
    cd ..\..
)

echo.
echo ========================================
echo ✅ 打包完成！
echo ========================================
echo.
echo 輸出位置:
echo   - 程式目錄: dist\ChroLens_Mimic\
echo   - ZIP 壓縮包: dist\ChroLens_Mimic.zip
echo.

pause
