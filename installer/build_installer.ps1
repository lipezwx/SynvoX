<#
  Builds the Windows installer for Synvox Invoice Extractor.

  Usage (PowerShell, from the repo root):
      .\installer\build_installer.ps1
      .\installer\build_installer.ps1 -Version 1.2.0

  Requires: Python 3.10+ and Inno Setup 6 (https://jrsoftware.org/isdl.php,
            or: winget install JRSoftware.InnoSetup)
  Output:   installer\Output\Synvox-Invoice-Extractor-Setup-<version>.exe
#>
param([string]$Version = "1.0.0")
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "==> Creating virtual environment" -ForegroundColor Cyan
if (-not (Test-Path .venv)) { python -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

Write-Host "==> Running tests" -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed" }

Write-Host "==> Generating brand assets" -ForegroundColor Cyan
& .\.venv\Scripts\python.exe scripts\make_assets.py

Write-Host "==> Building the app with PyInstaller" -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m PyInstaller installer\synvox.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

Write-Host "==> Compiling the installer with Inno Setup" -ForegroundColor Cyan
$iscc = (Get-Command iscc -ErrorAction SilentlyContinue).Source
if (-not $iscc) {
    $candidates = @("$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
                    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
                    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe")
    $iscc = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $iscc) { throw "Inno Setup 6 not found. Install it with: winget install JRSoftware.InnoSetup" }
& $iscc "/DAppVersion=$Version" installer\synvox.iss
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed" }

Write-Host "`nDone: installer\Output\Synvox-Invoice-Extractor-Setup-$Version.exe" -ForegroundColor Green
