@echo off
chcp 65001 > nul
echo ========================================
echo ChroLens_Mimic 打包工具
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] 開始打包...
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

pause
