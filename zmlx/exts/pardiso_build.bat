@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo === Build pardiso.dll (Intel MKL PARDISO) ===

REM [1] Locate Visual Studio
set "VCVARS="
if not defined DevEnvDir (
    for /f "usebackq tokens=*" %%i in (`where vswhere.exe 2^>nul`) do (
        for /f "usebackq tokens=*" %%p in (`"%%i" -latest -property installationPath`) do (
            if exist "%%p\VC\Auxiliary\Build\vcvars64.bat" set "VCVARS=%%p\VC\Auxiliary\Build\vcvars64.bat"
        )
    )
)
if not defined VCVARS (
    for %%v in (2026 18 2022 17 2019 16) do (
        for %%e in (Enterprise Professional Community BuildTools) do (
            if exist "C:\Program Files\Microsoft Visual Studio\%%v\%%e\VC\Auxiliary\Build\vcvars64.bat" (
                set "VCVARS=C:\Program Files\Microsoft Visual Studio\%%v\%%e\VC\Auxiliary\Build\vcvars64.bat"
                goto :vs_found
            )
        )
    )
)
:vs_found
if not defined VCVARS (
    echo [ERROR] Visual Studio not found. Install VS 2019/2022/2026.
    pause & exit /b 1
)
echo VS:   !VCVARS!

REM [2] Locate Intel MKL
set "MKLROOT="
set "MKLROOT=D:\miniconda3\envs\py313\Library"

for %%d in (
    "D:\miniconda3\envs\py313\Library"
) do (
    if exist "%%~d\lib\mkl_rt.lib" if exist "%%~d\include\mkl_pardiso.h" (
        set "MKLROOT=%%~d"
    )
)

if not defined MKLROOT (
    REM Fallback: check oneAPI default paths
    for %%d in (
        "C:\Program Files (x86)\Intel\oneAPI\mkl\latest"
        "C:\Program Files\Intel\oneAPI\mkl\latest"
    ) do (
        if exist "%%~d\lib\mkl_rt.lib" set "MKLROOT=%%~d"
    )
)

if not defined MKLROOT (
    echo [ERROR] Intel MKL not found.
    echo   pip install mkl mkl-devel
    echo   OR install Intel oneAPI Base Toolkit
    pause & exit /b 1
)
echo MKL:  !MKLROOT!

REM [3] Compile
call "!VCVARS!" >nul 2>&1
if errorlevel 1 ( echo [ERROR] vcvars failed & pause & exit /b 1 )

cl /std:c++17 /O2 /fp:fast /nologo /EHsc /MD /arch:AVX2 ^
   /D NDEBUG ^
   /I "!MKLROOT!\include" ^
   /LD pardiso.cpp ^
   /link /LIBPATH:"!MKLROOT!\lib" mkl_rt.lib /out:pardiso.dll

if errorlevel 1 (
    echo [ERROR] Build failed
    pause & exit /b %errorlevel%
)

echo.
echo === pardiso.dll built successfully ===
echo Output: %cd%\pardiso.dll
endlocal
