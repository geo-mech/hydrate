@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM  Build zml.dll with Clang (clang-cl)
REM  Needs: VS 2022/2026 + Clang tools + Boost built with clang-win
REM ============================================================

cd /d "%~dp0"

REM ---------- Temp directory ----------
set "TMPDIR=%TEMP%\zml_build_clang"
if not exist "%TMPDIR%" mkdir "%TMPDIR%"

REM ---------- Auto-detect Visual Studio ----------
if not defined DevEnvDir (
    echo [1/3] Locating Visual Studio ...
    set "VCVARS_FOUND="
    if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" (
        for /f "usebackq tokens=*" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -property installationPath`) do set "VS_PATH=%%i"
        if defined VS_PATH (
            if exist "!VS_PATH!\VC\Auxiliary\Build\vcvars64.bat" (
                set "VCVARS_FOUND=!VS_PATH!\VC\Auxiliary\Build\vcvars64.bat"
                echo   VS: !VS_PATH!
            )
        )
    )
    if not defined VCVARS_FOUND (
        for %%d in ("2026" "18" "2022" "17") do (
            if not defined VCVARS_FOUND (
                for %%e in (Enterprise Professional Community BuildTools) do (
                    if exist "C:\Program Files\Microsoft Visual Studio\%%~d\%%e\VC\Auxiliary\Build\vcvars64.bat" (
                        set "VCVARS_FOUND=C:\Program Files\Microsoft Visual Studio\%%~d\%%e\VC\Auxiliary\Build\vcvars64.bat"
                        echo   VS: C:\Program Files\Microsoft Visual Studio\%%~d\%%e
                    )
                )
            )
        )
    )
    if defined VCVARS_FOUND (
        call "!VCVARS_FOUND!" >nul 2>&1
    ) else (
        echo   [ERROR] VS not found
        pause & exit /b 1
    )
) else (
    echo [1/3] DevEnv ready
)

REM Check clang-cl is available
where clang-cl >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] clang-cl not found. Install "C++ Clang tools for Windows" in VS Installer.
    pause & exit /b 1
)

REM ---------- Paths ----------
set "BOOST_DIR=D:\boost_1_83_0"
set "BOOST_LIB=%BOOST_DIR%\stage\lib"
set "EIGEN_DIR=D:\eigen-5.0.0"

REM ---------- Build ----------
echo [2/3] Building zml.dll with Clang...
echo   C++17 ^| -O3 -march=native -ffast-math ^| OpenMP ^| Boost 1.83 (clang) ^| Eigen 5.0
echo   Obj dir: %TMPDIR%
echo.

clang-cl /std:c++17 /O2 ^
  -march=native -ffast-math ^
  /Oi /Ot /Oy /openmp /nologo /EHsc /MD ^
  /D NDEBUG /D BOOST_ALL_NO_LIB /D BOOST_THROW_EXCEPTION ^
  /I "..\..\..\.." /I "%BOOST_DIR%" /I "%EIGEN_DIR%" ^
  /Fo"%TMPDIR%\\" ^
  zml.cpp ^
  ..\..\..\system\NetworkTime.cpp ^
  ..\..\..\system\OpenUrl.cpp ^
  ..\..\..\system\SystemInfo.cpp ^
  ..\..\..\system\MakeUid.cpp ^
  ..\..\..\system\HardwareFingerprint.cpp ^
  /LD /link /LIBPATH:"%BOOST_LIB%" ^
  libboost_serialization-clangw22-mt-x64-1_83.lib ^
  libboost_filesystem-clangw22-mt-x64-1_83.lib ^
  libboost_nowide-clangw22-mt-x64-1_83.lib ^
  libboost_thread-clangw22-mt-x64-1_83.lib ^
  libboost_timer-clangw22-mt-x64-1_83.lib ^
  libboost_system-clangw22-mt-x64-1_83.lib ^
  libboost_chrono-clangw22-mt-x64-1_83.lib ^
  /out:zml.dll

if %ERRORLEVEL% EQU 0 (
    echo [3/3] Done
    echo   zml.dll [OK]
) else (
    echo [3/3] Failed
    echo   Error code: %ERRORLEVEL%
    pause & exit /b %ERRORLEVEL%
)
