# ChroLens Mimic - 驗證碼識別套件安裝腳本
# 此腳本會自動安裝 pytesseract 和相關套件

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ChroLens Mimic 驗證碼識別安裝工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 Python 是否安裝
Write-Host "[1/3] 檢查 Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ 找到 Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 未找到 Python，請先安裝 Python 3.7+" -ForegroundColor Red
    exit 1
}

# 安裝 Python 套件
Write-Host ""
Write-Host "[2/3] 安裝 Python 套件..." -ForegroundColor Yellow
Write-Host "  安裝中: pytesseract opencv-python" -ForegroundColor Gray

try {
    pip install pytesseract opencv-python --quiet
    Write-Host "  ✓ Python 套件安裝成功" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python 套件安裝失敗" -ForegroundColor Red
    Write-Host "  請手動執行: pip install pytesseract opencv-python" -ForegroundColor Yellow
}

# 檢查 Tesseract-OCR
Write-Host ""
Write-Host "[3/3] 檢查 Tesseract-OCR..." -ForegroundColor Yellow

$tesseractPaths = @(
    "C:\Program Files\Tesseract-OCR\tesseract.exe",
    "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "$env:LOCALAPPDATA\Tesseract-OCR\tesseract.exe"
)

$tesseractFound = $false
foreach ($path in $tesseractPaths) {
    if (Test-Path $path) {
        Write-Host "  ✓ 找到 Tesseract: $path" -ForegroundColor Green
        $tesseractFound = $true
        
        # 測試版本
        try {
            $version = & $path --version 2>&1 | Select-Object -First 1
            Write-Host "  版本: $version" -ForegroundColor Gray
        } catch {}
        
        break
    }
}

if (-not $tesseractFound) {
    Write-Host "  ⚠ 未找到 Tesseract-OCR" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "請手動安裝 Tesseract-OCR:" -ForegroundColor Cyan
    Write-Host "  1. 開啟瀏覽器" -ForegroundColor White
    Write-Host "  2. 前往: https://github.com/tesseract-ocr/tesseract/releases" -ForegroundColor White
    Write-Host "  3. 下載最新的 Windows 安裝檔 (tesseract-ocr-w64-setup-*.exe)" -ForegroundColor White
    Write-Host "  4. 執行安裝程式（記得勾選 'Add to PATH'）" -ForegroundColor White
    Write-Host ""
    
    # 詢問是否要開啟下載頁面
    $response = Read-Host "是否要開啟下載頁面? (Y/N)"
    if ($response -eq "Y" -or $response -eq "y") {
        Start-Process "https://github.com/tesseract-ocr/tesseract/releases"
    }
}

# 完成
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  安裝檢查完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($tesseractFound) {
    Write-Host "✓ 所有必要套件已就緒" -ForegroundColor Green
    Write-Host "  可以開始使用驗證碼識別功能了！" -ForegroundColor Green
} else {
    Write-Host "⚠ 請先安裝 Tesseract-OCR 才能使用驗證碼識別功能" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "使用說明:" -ForegroundColor Cyan
Write-Host "  1. 開啟 ChroLens Mimic 主程式" -ForegroundColor White
Write-Host "  2. 點擊「圖片管理器」" -ForegroundColor White
Write-Host "  3. 選擇驗證碼圖片" -ForegroundColor White
Write-Host "  4. 點擊「🔍 識別驗證碼」按鈕" -ForegroundColor White
Write-Host "  5. 結果會顯示在文字框中" -ForegroundColor White
Write-Host ""

Read-Host "按 Enter 鍵退出"
