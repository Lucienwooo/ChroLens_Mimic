@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ========================================
REM ChroLens_Mimic 自動打包工具 v3.0
REM 功能: 智能備份 + 使用者資料保留
REM ========================================

REM 切換到 bat 檔案所在目錄
cd /d "%~dp0"

REM ========================================
REM 設定版本號 (從 Python 檔案讀取)
REM ========================================
set CURRENT_VERSION=
for /f "tokens=2 delims==" %%a in ('findstr /C:"VERSION = " ChroLens_Mimic.py') do (
    set CURRENT_VERSION=%%a
)
set CURRENT_VERSION=%CURRENT_VERSION:"=%
set CURRENT_VERSION=%CURRENT_VERSION: =%

if "%CURRENT_VERSION%"=="" (
    echo [錯誤] 無法從 ChroLens_Mimic.py 讀取版本號
    pause
    exit /b 1
)

echo.
echo ========================================
echo ChroLens_Mimic 打包工具 v3.0
echo 當前版本: %CURRENT_VERSION%
echo ========================================
echo.

REM ========================================
REM 階段 1: 備份使用者資料和舊版本
REM ========================================
set TEMP_BACKUP=%TEMP%\ChroLens_Mimic_Backup_%RANDOM%

if exist "dist\ChroLens_Mimic" (
    echo [1/5] 備份現有資料...
    
    REM 讀取舊版本號
    set OLD_VERSION=
    if exist "dist\ChroLens_Mimic\version*.txt" (
        for /f "tokens=*" %%f in ('dir /b "dist\ChroLens_Mimic\version*.txt"') do (
            set "filename=%%f"
            set "OLD_VERSION=!filename:~7,-4!"
        )
    )
    
    if defined OLD_VERSION (
        echo 偵測到舊版本: !OLD_VERSION!
    ) else (
        echo 偵測到舊版本但無版本檔
    )
    
    REM 建立臨時備份目錄
    if exist "%TEMP_BACKUP%" rmdir /s /q "%TEMP_BACKUP%"
    mkdir "%TEMP_BACKUP%"
    
    REM 備份使用者資料
    if exist "dist\ChroLens_Mimic\scripts" (
        echo   正在備份 scripts...
        xcopy "dist\ChroLens_Mimic\scripts" "%TEMP_BACKUP%\scripts\" /E /I /Q /Y >nul 2>&1
    )
    if exist "dist\ChroLens_Mimic\user_config.json" (
        echo   正在備份 user_config.json...
        copy "dist\ChroLens_Mimic\user_config.json" "%TEMP_BACKUP%\" >nul 2>&1
    )
    if exist "dist\ChroLens_Mimic\last_script.txt" (
        echo   正在備份 last_script.txt...
        copy "dist\ChroLens_Mimic\last_script.txt" "%TEMP_BACKUP%\" >nul 2>&1
    )
    
    REM 備份舊版程式用於版本回退
    if defined OLD_VERSION (
        if exist "dist\ChroLens_Mimic\_internal" (
            echo   正在備份舊版核心檔案...
            xcopy "dist\ChroLens_Mimic\_internal" "%TEMP_BACKUP%\_internal\" /E /I /Q /Y >nul 2>&1
        )
        if exist "dist\ChroLens_Mimic\ChroLens_Mimic.exe" (
            echo   正在備份舊版主程式...
            copy "dist\ChroLens_Mimic\ChroLens_Mimic.exe" "%TEMP_BACKUP%\" >nul 2>&1
        )
    )
    
    echo 備份完成
    echo.
) else (
    echo [1/5] 首次打包，跳過備份
    echo.
)

REM ========================================
REM 階段 2: 清理舊檔案
REM ========================================
echo [2/5] 清理舊檔案...

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "ChroLens_Mimic.spec" del /q "ChroLens_Mimic.spec"

echo 清理完成
echo.

REM ========================================
REM 階段 3: PyInstaller 打包
REM ========================================
echo [3/5] 開始打包 ChroLens_Mimic %CURRENT_VERSION%...
echo.

python -m PyInstaller --clean --noconsole --onedir -y ^
    --icon="../umi_奶茶色.ico" ^
    --add-data "../umi_奶茶色.ico;." ^
    --add-data "TTF;TTF" ^
    --add-data "recorder.py;." ^
    --add-data "lang.py;." ^
    --add-data "script_io.py;." ^
    --add-data "about.py;." ^
    --add-data "mini.py;." ^
    --add-data "window_selector.py;." ^
    --add-data "script_parser.py;." ^
    --add-data "config_manager.py;." ^
    --add-data "hotkey_manager.py;." ^
    --add-data "script_editor_methods.py;." ^
    --add-data "script_manager.py;." ^
    --add-data "ui_components.py;." ^
    --add-data "visual_script_editor.py;." ^
    --hidden-import=ttkbootstrap ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageTk ^
    --hidden-import=pynput ^
    --hidden-import=pynput.keyboard ^
    --hidden-import=pynput.mouse ^
    --hidden-import=psutil ^
    --hidden-import=win32gui ^
    --hidden-import=win32con ^
    --hidden-import=win32api ^
    --hidden-import=pywintypes ^
    --collect-all=ttkbootstrap ^
    --name "ChroLens_Mimic" ^
    "ChroLens_Mimic.py"

if errorlevel 1 (
    echo.
    echo [錯誤] 打包失敗！
    if exist "%TEMP_BACKUP%" (
        echo 正在恢復備份...
        mkdir "dist\ChroLens_Mimic"
        xcopy "%TEMP_BACKUP%\*" "dist\ChroLens_Mimic\" /E /I /Q /Y >nul 2>&1
        rmdir /s /q "%TEMP_BACKUP%"
        echo 已恢復舊版本
    )
    pause
    exit /b 1
)

echo.
echo [成功] 打包完成！
echo.

REM ========================================
REM 階段 4: 建立版本資訊檔
REM ========================================
echo [4/5] 建立版本資訊...

(
echo ChroLens_Mimic
echo.
echo 當前版本: %CURRENT_VERSION%
echo 更新日期: %DATE% %TIME%
echo.
echo ========================================
echo 版本更新紀錄
echo ========================================
echo.
echo [2.6.4] - 2025/11/03
echo - 重新設計打包架構，簡化流程
echo - 修正：版本資訊檔改為 version版本號.txt
echo - 修正：備份資料夾改為 backup\版本號\
echo - 移除：所有多餘的 .md 說明文件
echo - 改進：使用者資料自動保留
echo.
echo [2.6.3] - 2025/11/03
echo - 修復：腳本寫入錯誤處理
echo - 修復：視窗提示大小問題
echo - 改進：統一檔名為 ChroLens_Mimic
echo.
echo ========================================
echo 版本還原說明
echo ========================================
echo.
echo 如需還原舊版本：
echo 1. 進入 backup\版本號\ 資料夾
echo 2. 將 _internal 資料夾複製並覆蓋到程式目錄
echo 3. 將 ChroLens_Mimic.exe 複製並覆蓋到程式目錄
echo 4. 重新啟動程式即可還原
) > "dist\ChroLens_Mimic\version%CURRENT_VERSION%.txt"

echo   ✓ version%CURRENT_VERSION%.txt 已建立
echo.

REM ========================================
REM 階段 5: 恢復使用者資料與建立備份
REM ========================================
echo [5/5] 恢復使用者資料與建立備份...

REM 恢復使用者資料
if exist "%TEMP_BACKUP%\scripts" (
    xcopy "%TEMP_BACKUP%\scripts" "dist\ChroLens_Mimic\scripts\" /E /I /Q /Y >nul 2>&1
    echo   ✓ 已恢復 scripts
)
if exist "%TEMP_BACKUP%\user_config.json" (
    copy "%TEMP_BACKUP%\user_config.json" "dist\ChroLens_Mimic\" >nul 2>&1
    echo   ✓ 已恢復 user_config.json
)
if exist "%TEMP_BACKUP%\last_script.txt" (
    copy "%TEMP_BACKUP%\last_script.txt" "dist\ChroLens_Mimic\" >nul 2>&1
    echo   ✓ 已恢復 last_script.txt
)

REM 建立舊版本備份
if defined OLD_VERSION (
    if exist "%TEMP_BACKUP%\_internal" (
        echo.
        echo 建立舊版本備份...
        
        if not exist "dist\ChroLens_Mimic\backup" mkdir "dist\ChroLens_Mimic\backup"
        if not exist "dist\ChroLens_Mimic\backup\%OLD_VERSION%" mkdir "dist\ChroLens_Mimic\backup\%OLD_VERSION%"
        
        REM 使用 PowerShell 進行智能差異備份
        powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$oldPath = '%TEMP_BACKUP%\_internal'; " ^
        "$newPath = '%CD%\dist\ChroLens_Mimic\_internal'; " ^
        "$backupPath = '%CD%\dist\ChroLens_Mimic\backup\%OLD_VERSION%\_internal'; " ^
        "$changedCount = 0; " ^
        "$removedCount = 0; " ^
        "if (Test-Path $oldPath) { " ^
        "    $oldFiles = Get-ChildItem -Path $oldPath -Recurse -File; " ^
        "    foreach ($oldFile in $oldFiles) { " ^
        "        $relativePath = $oldFile.FullName.Substring($oldPath.Length + 1); " ^
        "        $newFile = Join-Path $newPath $relativePath; " ^
        "        $shouldBackup = $false; " ^
        "        if (Test-Path $newFile) { " ^
        "            try { " ^
        "                $oldHash = (Get-FileHash $oldFile.FullName -Algorithm MD5).Hash; " ^
        "                $newHash = (Get-FileHash $newFile -Algorithm MD5).Hash; " ^
        "                if ($oldHash -ne $newHash) { $shouldBackup = $true; $changedCount++; } " ^
        "            } catch { $shouldBackup = $true; $changedCount++; } " ^
        "        } else { $shouldBackup = $true; $removedCount++; } " ^
        "        if ($shouldBackup) { " ^
        "            $backupFile = Join-Path $backupPath $relativePath; " ^
        "            $backupDir = Split-Path $backupFile -Parent; " ^
        "            if (!(Test-Path $backupDir)) { New-Item -ItemType Directory -Path $backupDir -Force | Out-Null }; " ^
        "            Copy-Item $oldFile.FullName $backupFile -Force; " ^
        "        } " ^
        "    } " ^
        "} " ^
        "Write-Host \"  變更檔案: $changedCount 個\" -ForegroundColor Yellow; " ^
        "Write-Host \"  移除檔案: $removedCount 個\" -ForegroundColor Red;"
        
        REM 備份舊版 EXE
        if exist "%TEMP_BACKUP%\ChroLens_Mimic.exe" (
            copy "%TEMP_BACKUP%\ChroLens_Mimic.exe" "dist\ChroLens_Mimic\backup\%OLD_VERSION%\" >nul 2>&1
            echo   ✓ 已備份舊版 EXE: backup\%OLD_VERSION%\ChroLens_Mimic.exe
        )
    )
)

REM 清理臨時備份
if exist "%TEMP_BACKUP%" (
    rmdir /s /q "%TEMP_BACKUP%"
)

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 📦 輸出檔案:
echo   - 主程式: dist\ChroLens_Mimic\ChroLens_Mimic.exe
echo   - 版本檔: dist\ChroLens_Mimic\version%CURRENT_VERSION%.txt
if defined OLD_VERSION (
    echo   - 備份: dist\ChroLens_Mimic\backup\%OLD_VERSION%\
)
echo.
echo 📂 目錄結構:
echo   ChroLens_Mimic\
echo   ├── ChroLens_Mimic.exe     ✅ 主程式
echo   ├── version%CURRENT_VERSION%.txt        ✅ 版本資訊
echo   ├── _internal\             ✅ 程式核心
if exist "dist\ChroLens_Mimic\scripts" (
    echo   ├── scripts\               ✅ 使用者腳本 (已保留^)
)
if exist "dist\ChroLens_Mimic\user_config.json" (
    echo   ├── user_config.json       ✅ 使用者設定 (已保留^)
)
if exist "dist\ChroLens_Mimic\last_script.txt" (
    echo   ├── last_script.txt        ✅ 最後腳本 (已保留^)
)
if defined OLD_VERSION (
    echo   └── backup\                ✅ 舊版備份
    echo       └── %OLD_VERSION%\
    echo           ├── ChroLens_Mimic.exe
    echo           └── _internal\     (僅變更的檔案^)
)
echo.
echo ========================================
pause
