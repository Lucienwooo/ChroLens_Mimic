@echo off
chcp 65001 > nul
echo ========================================
echo 強制清理工具
echo ========================================
echo.
echo [警告] 此工具將強制關閉檔案總管以釋放檔案鎖定
echo [提示] 檔案總管會自動重新啟動
echo.
echo 按任意鍵繼續...
pause >nul

cd /d "%~dp0"

echo [1/3] 關閉 ChroLens_Mimic.exe...
taskkill /F /IM ChroLens_Mimic.exe 2>nul
timeout /t 1 /nobreak >nul

echo [2/3] 重啟檔案總管以釋放檔案鎖定...
taskkill /F /IM explorer.exe 2>nul
timeout /t 2 /nobreak >nul

echo [3/3] 清理 dist 和 build 目錄...
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul
timeout /t 1 /nobreak >nul

echo.
echo [完成] 啟動檔案總管...
start explorer.exe

echo.
echo ========================================
echo 清理完成！
echo ========================================
echo.
echo 現在可以執行打包腳本了
echo.
pause
