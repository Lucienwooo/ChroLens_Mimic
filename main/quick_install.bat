@echo off
chcp 65001 >nul
echo ========================================
echo   ChroLens Mimic 驗證碼識別快速安裝
echo ========================================
echo.

echo [1/3] 安裝 Python 套件...
pip install pytesseract opencv-python pillow numpy
if %errorlevel% neq 0 (
    echo ✗ Python 套件安裝失敗
    pause
    exit /b 1
)
echo ✓ Python 套件安裝成功
echo.

echo [2/3] 檢查 Tesseract-OCR...
where tesseract >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ 找到 Tesseract
    tesseract --version
) else (
    if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
        echo ✓ 找到 Tesseract: C:\Program Files\Tesseract-OCR\tesseract.exe
        "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
    ) else if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
        echo ✓ 找到 Tesseract: C:\Program Files (x86)\Tesseract-OCR\tesseract.exe
        "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" --version
    ) else (
        echo.
        echo ⚠ 未找到 Tesseract-OCR
        echo.
        echo 請下載並安裝 Tesseract-OCR:
        echo https://github.com/UB-Mannheim/tesseract/wiki
        echo.
        set /p "openurl=是否要開啟下載頁面? (Y/N): "
        if /i "%openurl%"=="Y" (
            start https://github.com/UB-Mannheim/tesseract/wiki
        )
        echo.
        echo 安裝 Tesseract 後，請重新執行此腳本
        pause
        exit /b 1
    )
)
echo.

echo [3/3] 測試安裝...
python -c "import pytesseract; import cv2; print('✓ 所有套件正常')"
if %errorlevel% neq 0 (
    echo ✗ 測試失敗
    pause
    exit /b 1
)
echo.

echo ========================================
echo   安裝完成！
echo ========================================
echo.
echo ✓ Python 套件已安裝
echo ✓ Tesseract-OCR 已就緒
echo.
echo 使用方法:
echo 1. 開啟 ChroLens Mimic
echo 2. 點擊「圖片管理器」
echo 3. 選擇驗證碼圖片
echo 4. 點擊「🔍 識別驗證碼」
echo.
pause
