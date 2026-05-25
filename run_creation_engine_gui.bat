@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
    echo Python 3 is not installed.
    echo Install Python from https://www.python.org/downloads/windows/ and re-run this file.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating local virtual environment...
    call %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

set "VENV_PY=.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo Virtual environment Python executable missing.
    pause
    exit /b 1
)

echo Installing Creation Engine runtime dependencies...
call "%VENV_PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo Failed to update pip tooling.
    pause
    exit /b 1
)

call "%VENV_PY%" -m pip install --upgrade numpy pillow
if errorlevel 1 (
    echo Failed to install required GUI packages.
    pause
    exit /b 1
)

call "%VENV_PY%" -m pip install --upgrade .
if errorlevel 1 (
    echo Failed to install Creation Engine package.
    pause
    exit /b 1
)

if not exist "assets" mkdir "assets"
if not exist "assets\materials" mkdir "assets\materials"
if not exist "assets\maps" mkdir "assets\maps"
if not exist "assets\meshes" mkdir "assets\meshes"
if not exist "assets\ui" mkdir "assets\ui"

call "%VENV_PY%" -m creation_engine.cli list-backends >nul
if errorlevel 1 (
    echo Installation check failed: CLI import test did not pass.
    pause
    exit /b 1
)

echo Launching Creation Engine GUI...
call "%VENV_PY%" -m creation_engine.cli gui --output assets %*
if errorlevel 1 (
    echo GUI exited with an error.
    pause
    exit /b 1
)

endlocal
