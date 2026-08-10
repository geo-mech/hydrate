@echo off
setlocal
REM Build zml.so via WSL2
cd /d "%~dp0"

REM Check WSL
wsl --status >nul 2>&1
if errorlevel 1 (
    echo [ERROR] WSL not available
    pause
    exit /b 1
)

REM Build: wsl -> build.sh in current dir
REM The cd sets the working dir; wsl inherits it via --cd (WSL2 supports this)
echo Building zml.so via WSL...
wsl bash -c "cd /mnt/c/Users/zhaob/OneDrive/MyProjects/zml/projects/zml/zmlx/exts && bash build.sh"

if errorlevel 1 (
    echo [ERROR] WSL build failed
    pause
    exit /b 1
)

echo zml.so built successfully
dir zml.so 2>nul
