@echo off
setlocal
title Build Synvox installer
cd /d "%~dp0"

echo ==================================================
echo   Synvox Invoice Extractor - one-click installer build
echo ==================================================
echo.

REM ---------- 1. Python ----------
set "PYEXE="
call :find_python
if not defined PYEXE (
    echo [1/3] Python not found. Installing Python 3.12 with winget...
    winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
    call :find_python
)
if not defined PYEXE (
    echo.
    echo Python was installed but this window cannot see it yet.
    echo Close this window and double-click BUILD-INSTALLER.bat again.
    goto :fail_soft
)
for %%I in ("%PYEXE%") do set "PATH=%%~dpI;%%~dpIScripts;%PATH%"
echo [1/3] Python OK: %PYEXE%

REM ---------- 2. Inno Setup ----------
set "ISCC="
call :find_iscc
if not defined ISCC (
    echo [2/3] Inno Setup not found. Installing it with winget...
    winget install --id JRSoftware.InnoSetup -e --silent --accept-package-agreements --accept-source-agreements
    call :find_iscc
)
if not defined ISCC (
    echo.
    echo Could not find Inno Setup. Install it from https://jrsoftware.org/isdl.php
    echo and run this file again.
    goto :fail_soft
)
for %%I in ("%ISCC%") do set "PATH=%%~dpI;%PATH%"
echo [2/3] Inno Setup OK: %ISCC%

REM ---------- 3. Build ----------
echo [3/3] Building (first run downloads about 500 MB of packages, 5-15 min)...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "installer\build_installer.ps1" -SkipTests
if errorlevel 1 goto :fail

echo.
echo ==================================================
echo   DONE. Your installer is in installer\Output
echo ==================================================
explorer "installer\Output"
pause
exit /b 0

:fail
echo.
echo Build FAILED. Scroll up to see the first error message.
:fail_soft
pause
exit /b 1

:find_python
set "PYEXE="
for /f "delims=" %%I in ('py -3 -c "import sys;print(sys.executable)" 2^>nul') do set "PYEXE=%%I"
if defined PYEXE exit /b 0
for %%P in ("%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%ProgramFiles%\Python312\python.exe" "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" "%LOCALAPPDATA%\Programs\Python\Python311\python.exe") do if exist %%P if not defined PYEXE set "PYEXE=%%~P"
if defined PYEXE exit /b 0
for /f "delims=" %%I in ('where python 2^>nul') do if not defined PYEXE (
    "%%I" -c "import sys" >nul 2>&1 && set "PYEXE=%%I"
)
exit /b 0

:find_iscc
set "ISCC="
for %%P in ("%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" "%ProgramFiles%\Inno Setup 6\ISCC.exe" "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe") do if exist %%P if not defined ISCC set "ISCC=%%~P"
if defined ISCC exit /b 0
for /f "delims=" %%I in ('where iscc 2^>nul') do if not defined ISCC set "ISCC=%%I"
exit /b 0
