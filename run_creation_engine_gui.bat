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

echo Installing Creation Engine dependencies...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to update pip.
    pause
    exit /b 1
)

call ".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 (
    echo Failed to install Creation Engine.
    pause
    exit /b 1
)

echo Launching Creation Engine GUI...
call ".venv\Scripts\python.exe" -m creation_engine.cli gui --output assets %*
if errorlevel 1 (
    echo GUI exited with an error.
    pause
    exit /b 1
)

endlocal
