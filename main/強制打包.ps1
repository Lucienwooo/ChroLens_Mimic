# 強制清理並打包
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ChroLens_Mimic 強制清理並打包" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

# 步驟1: 關閉程序
Write-Host "[1/5] 關閉相關程序..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.Name -like "*ChroLens_Mimic*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# 步驟2: 關閉 Explorer
Write-Host "[2/5] 關閉檔案總管以釋放檔案鎖定..." -ForegroundColor Yellow
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 步驟3: 強制刪除目錄
Write-Host "[3/5] 刪除 dist 和 build 目錄..." -ForegroundColor Yellow
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# 步驟4: 重啟 Explorer
Write-Host "[4/5] 重啟檔案總管..." -ForegroundColor Yellow
Start-Process explorer.exe
Start-Sleep -Seconds 2

# 步驟5: 執行打包
Write-Host "[5/5] 開始打包..." -ForegroundColor Green
Write-Host ""
python build_simple.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "打包成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    if (Test-Path "dist\ChroLens_Mimic\ChroLens_Mimic.exe") {
        Write-Host "輸出位置:" -ForegroundColor Cyan
        Write-Host "  EXE: dist\ChroLens_Mimic\ChroLens_Mimic.exe" -ForegroundColor White
    }
    if (Test-Path "dist\ChroLens_Mimic.zip") {
        Write-Host "  ZIP: dist\ChroLens_Mimic.zip" -ForegroundColor White
    }
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "打包失敗！" -ForegroundColor Red  
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
}

Write-Host "按任意鍵結束..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
