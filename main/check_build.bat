@echo off
chcp 65001 > nul
echo.
echo 檢查打包結果...
echo.

if exist "dist\ChroLens_Mimic\ChroLens_Mimic.exe" (
    echo [92m✓ ChroLens_Mimic.exe 存在[0m
    
    echo.
    echo 檔案資訊:
    for %%F in ("dist\ChroLens_Mimic\ChroLens_Mimic.exe") do (
        set "size=%%~zF"
        set /a "sizeMB=!size! / 1048576"
        echo   大小: !sizeMB! MB
        echo   修改時間: %%~tF
    )
    
    echo.
    echo 複製診斷工具...
    copy /Y "check_hotkey.py" "dist\ChroLens_Mimic\" > nul
    if exist "dist\ChroLens_Mimic\check_hotkey.py" (
        echo [92m✓ 診斷工具已複製[0m
    )
    
    echo.
    echo dist 目錄內容:
    dir /B "dist\ChroLens_Mimic" | findstr /V "^_internal$"
    
    echo.
    echo [92m打包成功！[0m
    
) else (
    echo [91m✗ ChroLens_Mimic.exe 不存在[0m
    echo.
    echo 請檢查 build_log.txt
    if exist "build_log.txt" (
        echo.
        echo 最後 20 行錯誤日誌:
        powershell -Command "Get-Content build_log.txt -Tail 20"
    )
)

echo.
pause
