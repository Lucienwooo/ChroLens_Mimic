# PowerShell Script - Force Clean and Build
Write-Host "========================================"
Write-Host "ChroLens_Mimic Force Clean and Build"
Write-Host "========================================"
Write-Host ""

Set-Location $PSScriptRoot

Write-Host "[1/5] Closing related processes..."
Get-Process | Where-Object {$_.Name -like "*ChroLens_Mimic*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

Write-Host "[2/5] Closing Explorer to release file locks..."
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "[3/5] Deleting dist and build directories..."
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

Write-Host "[4/5] Restarting Explorer..."
Start-Process explorer.exe
Start-Sleep -Seconds 2

Write-Host "[5/5] Starting build process..."
Write-Host ""
python build_simple.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================"
    Write-Host "Build Successful!"
    Write-Host "========================================"
    Write-Host ""
    
    if (Test-Path "dist\ChroLens_Mimic\ChroLens_Mimic.exe") {
        Write-Host "Output location:"
        Write-Host "  EXE: dist\ChroLens_Mimic\ChroLens_Mimic.exe"
    }
    if (Test-Path "dist\ChroLens_Mimic.zip") {
        Write-Host "  ZIP: dist\ChroLens_Mimic.zip"
    }
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================"
    Write-Host "Build Failed!"
    Write-Host "========================================"
    Write-Host ""
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
