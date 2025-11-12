@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: 設定顏色
set "GREEN=[92m"
set "YELLOW=[93m"
set "CYAN=[96m"
set "RED=[91m"
set "RESET=[0m"
set "BOLD=[1m"

:: 動態進度條函數設定
set "BAR_LENGTH=50"
set "CURSOR_HIDE=[?25l"
set "CURSOR_SHOW=[?25h"

:: 清除畫面並隱藏游標
cls
echo %CURSOR_HIDE%

echo.
echo %BOLD%%CYAN%╔════════════════════════════════════════════════════════╗%RESET%
echo %BOLD%%CYAN%║       ChroLens_Mimic 打包工具 v2.6.3                    ║%RESET%
echo %BOLD%%CYAN%╚════════════════════════════════════════════════════════╝%RESET%
echo.
echo.

:: ============================================
:: 步驟 1: 檢查 Python 環境 (0-20%)
:: ============================================
call :ShowProgress 0 "檢查 Python 環境"
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo %RED%✗ Python 未安裝或未加入 PATH%RESET%
    echo %CURSOR_SHOW%
    pause
    exit /b 1
)
for /l %%i in (1,1,20) do (
    call :ShowProgress %%i "檢查 Python 環境"
    timeout /t 0 /nobreak > nul
)
echo.
echo %GREEN%✓ Python 環境正常%RESET%
echo.

:: ============================================
:: 步驟 2: 清理舊檔案 (20-40%)
:: ============================================
for /l %%i in (21,1,40) do (
    call :ShowProgress %%i "清理舊檔案"
    if %%i==25 if exist "build" rmdir /s /q "build" 2>nul
    if %%i==30 if exist "dist" rmdir /s /q "dist" 2>nul
    timeout /t 0 /nobreak > nul
)
echo.
echo %GREEN%✓ 清理完成%RESET%
echo.

:: ============================================
:: 步驟 3: 執行 PyInstaller 打包 (40-80%)
:: ============================================
call :ShowProgress 40 "執行 PyInstaller 打包"
echo.
echo %CYAN%正在打包，請稍候...%RESET%

:: 啟動背景打包並顯示動態進度條
start /b "" python build_simple.py > build_log.txt 2>&1

:: 動態顯示進度條（模擬打包過程）
set /a "progress=40"
:PackingLoop
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I "python.exe" >NUL
if %errorlevel% equ 0 (
    if !progress! lss 80 (
        set /a "progress+=1"
        call :ShowProgress !progress! "執行 PyInstaller 打包"
        timeout /t 1 /nobreak > nul
        goto PackingLoop
    ) else (
        timeout /t 1 /nobreak > nul
        goto PackingLoop
    )
)

:: 等待打包完成
timeout /t 1 /nobreak > nul
call :ShowProgress 80 "執行 PyInstaller 打包"

:: 檢查打包結果
if not exist "dist\ChroLens_Mimic\ChroLens_Mimic.exe" (
    echo.
    echo %RED%✗ 打包失敗，請檢查 build_log.txt%RESET%
    echo %CURSOR_SHOW%
    pause
    exit /b 1
)
echo.
echo %GREEN%✓ 打包完成%RESET%
echo.

:: ============================================
:: 步驟 4: 驗證輸出 (80-95%)
:: ============================================
for /l %%i in (81,1,95) do (
    call :ShowProgress %%i "驗證輸出檔案"
    if %%i==85 (
        if not exist "dist\ChroLens_Mimic\ChroLens_Mimic.exe" (
            echo.
            echo %RED%✗ 找不到 ChroLens_Mimic.exe%RESET%
            echo %CURSOR_SHOW%
            pause
            exit /b 1
        )
    )
    if %%i==90 (
        if not exist "dist\ChroLens_Mimic.zip" (
            echo.
            echo %RED%✗ 找不到 ChroLens_Mimic.zip%RESET%
            echo %CURSOR_SHOW%
            pause
            exit /b 1
        )
    )
    timeout /t 0 /nobreak > nul
)
echo.
echo %GREEN%✓ 檔案驗證通過%RESET%
echo.

:: ============================================
:: 步驟 5: 完成 (95-100%)
:: ============================================
for /l %%i in (96,1,100) do (
    call :ShowProgress %%i "打包完成"
    timeout /t 0 /nobreak > nul
)
echo.
echo %CURSOR_SHOW%
echo.
echo %BOLD%%GREEN%╔════════════════════════════════════════════════════════╗%RESET%
echo %BOLD%%GREEN%║                 打包成功！                            ║%RESET%
echo %BOLD%%GREEN%╚════════════════════════════════════════════════════════╝%RESET%
echo.

:: 顯示檔案資訊
echo %CYAN%輸出檔案:%RESET%
echo.
for %%F in ("dist\ChroLens_Mimic\ChroLens_Mimic.exe") do (
    set "size=%%~zF"
    set /a "sizeMB=!size! / 1048576"
    echo   %YELLOW%►%RESET% ChroLens_Mimic.exe  %GREEN%(!sizeMB! MB)%RESET%
)
for %%F in ("dist\ChroLens_Mimic.zip") do (
    set "size=%%~zF"
    set /a "sizeMB=!size! / 1048576"
    echo   %YELLOW%►%RESET% ChroLens_Mimic.zip  %GREEN%(!sizeMB! MB)%RESET%
)
echo.
echo %CYAN%位置:%RESET% %cd%\dist\
echo.

:: 詢問是否開啟資料夾
echo.
set /p "openFolder=%YELLOW%是否開啟 dist 資料夾? (Y/N): %RESET%"
if /i "!openFolder!"=="Y" (
    start "" "dist"
)

echo.
echo %GREEN%按任意鍵結束...%RESET%
pause > nul
goto :eof

:: ============================================
:: 動態進度條函數
:: 參數: %1=進度百分比(0-100), %2=當前步驟描述
:: ============================================
:ShowProgress
setlocal
set /a "percent=%1"
set "task=%~2"

:: 計算進度條長度
set /a "filled=percent*BAR_LENGTH/100"
set /a "empty=BAR_LENGTH-filled"

:: 建立進度條字串
set "bar="
for /l %%i in (1,1,%filled%) do set "bar=!bar!█"
for /l %%i in (1,1,%empty%) do set "bar=!bar!░"

:: 使用 ANSI 轉義序列移動游標到進度條行（向上3行）
echo [3A
echo %CYAN%進度: [%YELLOW%!bar!%CYAN%] %BOLD%%GREEN%!percent!%%%RESET%
echo %YELLOW%!task!...%RESET%
echo.

endlocal
goto :eof
