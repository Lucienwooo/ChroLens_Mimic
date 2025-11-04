@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ChroLens_Mimic 更新器
REM 參數: %1=ZIP路徑 %2=安裝目錄 %3=EXE名稱

set "ZIP_PATH=%~1"
set "INSTALL_DIR=%~2"
set "EXE_NAME=%~3"

echo.
echo ========================================
echo   ChroLens_Mimic 更新器
echo ========================================
echo.

REM 等待主程式關閉
echo [1/5] 等待主程式關閉...
timeout /t 3 /nobreak >nul

REM 檢查 ZIP 檔案
if not exist "%ZIP_PATH%" (
    echo [X] 錯誤：找不到更新檔案
    echo     %ZIP_PATH%
    pause
    exit /b 1
)

echo [2/5] 備份使用者資料...
REM 備份 scripts 目錄
if exist "%INSTALL_DIR%\scripts" (
    xcopy "%INSTALL_DIR%\scripts" "%INSTALL_DIR%\..\scripts_backup\" /E /I /Y >nul 2>&1
    echo     [OK] 已備份 scripts
)

REM 備份設定檔
if exist "%INSTALL_DIR%\user_config.json" (
    copy "%INSTALL_DIR%\user_config.json" "%INSTALL_DIR%\..\user_config_backup.json" /Y >nul 2>&1
    echo     [OK] 已備份 user_config.json
)

if exist "%INSTALL_DIR%\last_script.txt" (
    copy "%INSTALL_DIR%\last_script.txt" "%INSTALL_DIR%\..\last_script_backup.txt" /Y >nul 2>&1
    echo     [OK] 已備份 last_script.txt
)

echo [3/5] 刪除舊版本...
REM 刪除 _internal 目錄（最大的）
if exist "%INSTALL_DIR%\_internal" (
    rd /s /q "%INSTALL_DIR%\_internal" 2>nul
    echo     [OK] 已刪除 _internal
)

REM 刪除主程式
if exist "%INSTALL_DIR%\%EXE_NAME%" (
    del /f /q "%INSTALL_DIR%\%EXE_NAME%" 2>nul
    echo     [OK] 已刪除主程式
)

REM 刪除舊版本檔
for %%f in ("%INSTALL_DIR%\version*.txt") do (
    del /f /q "%%f" 2>nul
)

REM 刪除 updater.exe
if exist "%INSTALL_DIR%\updater.exe" (
    del /f /q "%INSTALL_DIR%\updater.exe" 2>nul
)

echo [4/5] 安裝新版本...
REM 使用 PowerShell 解壓縮
powershell -command "Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%INSTALL_DIR%\..\temp_update' -Force" >nul 2>&1

if errorlevel 1 (
    echo [X] 解壓縮失敗
    pause
    exit /b 1
)

REM 複製檔案（ZIP 內應該有 ChroLens_Mimic 資料夾）
if exist "%INSTALL_DIR%\..\temp_update\ChroLens_Mimic" (
    echo     正在複製檔案...
    xcopy "%INSTALL_DIR%\..\temp_update\ChroLens_Mimic\*.*" "%INSTALL_DIR%\" /E /I /Y >nul 2>&1
    rd /s /q "%INSTALL_DIR%\..\temp_update" 2>nul
    echo     [OK] 已安裝新版本
) else (
    echo [X] ZIP 格式錯誤：找不到 ChroLens_Mimic 資料夾
    rd /s /q "%INSTALL_DIR%\..\temp_update" 2>nul
    pause
    exit /b 1
)

echo [5/5] 恢復使用者資料...
REM 恢復 scripts
if exist "%INSTALL_DIR%\..\scripts_backup" (
    xcopy "%INSTALL_DIR%\..\scripts_backup" "%INSTALL_DIR%\scripts\" /E /I /Y >nul 2>&1
    rd /s /q "%INSTALL_DIR%\..\scripts_backup" 2>nul
    echo     [OK] 已恢復 scripts
)

REM 恢復設定檔
if exist "%INSTALL_DIR%\..\user_config_backup.json" (
    copy "%INSTALL_DIR%\..\user_config_backup.json" "%INSTALL_DIR%\user_config.json" /Y >nul 2>&1
    del /f /q "%INSTALL_DIR%\..\user_config_backup.json" 2>nul
    echo     [OK] 已恢復 user_config.json
)

if exist "%INSTALL_DIR%\..\last_script_backup.txt" (
    copy "%INSTALL_DIR%\..\last_script_backup.txt" "%INSTALL_DIR%\last_script.txt" /Y >nul 2>&1
    del /f /q "%INSTALL_DIR%\..\last_script_backup.txt" 2>nul
    echo     [OK] 已恢復 last_script.txt
)

echo.
echo ========================================
echo   [OK] 更新完成！
echo ========================================
echo.

REM 刪除更新檔案
del /f /q "%ZIP_PATH%" 2>nul

REM 重新啟動程式
echo 正在重新啟動程式...
timeout /t 2 /nobreak >nul
start "" "%INSTALL_DIR%\%EXE_NAME%"

exit /b 0
