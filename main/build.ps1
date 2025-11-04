# ChroLens_Mimic 快速打包腳本
# 使用方式: .\build.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ChroLens_Mimic 快速打包工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 Python 是否安裝
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ 錯誤: 找不到 Python" -ForegroundColor Red
    Write-Host "請先安裝 Python 3.8 或更新版本" -ForegroundColor Yellow
    pause
    exit 1
}

# 檢查 build.py 是否存在
if (-not (Test-Path "build.py")) {
    Write-Host "✗ 錯誤: 找不到 build.py" -ForegroundColor Red
    Write-Host "請在 main 目錄中執行此腳本" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host ""
Write-Host "開始打包..." -ForegroundColor Cyan
Write-Host ""

# 執行 build.py
python build.py

# 檢查執行結果
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ 打包成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "輸出目錄: dist\ChroLens_Mimic" -ForegroundColor Yellow
    Write-Host ""
    
    # 詢問是否開啟目錄
    $openDir = Read-Host "是否開啟輸出目錄? (Y/N)"
    if ($openDir -eq "Y" -or $openDir -eq "y") {
        Start-Process "dist\ChroLens_Mimic"
    }
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ 打包失敗！" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "請檢查錯誤訊息並重試" -ForegroundColor Yellow
}

Write-Host ""
pause
