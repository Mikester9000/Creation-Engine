@echo off
setlocal EnableExtensions

cd /d "%~dp0"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PYTHON_CMD=py -3"
) else (
    where python >nul 2>nul
    if %ERRORLEVEL%==0 (
        set "PYTHON_CMD=python"
    ) else (
        echo Python 3 is not installed.
        echo Install Python from https://www.python.org/downloads/windows/ and re-run this file.
        pause
        exit /b 1
    )
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
set "VENV_PIP=.venv\Scripts\pip.exe"

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

call "%VENV_PY%" -m pip install .
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

call "%VENV_PY%" -m creation_engine.cli list-backends >nul 2>nul
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
