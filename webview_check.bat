@echo off
REM WebView Checker - Windows Batch Wrapper
REM Usage: webview_check.bat <apk_file> [options]

setlocal enabledelayedexpansion

if "%1"=="" (
    echo.
    echo Usage: webview_check.bat ^<apk_file^> [options]
    echo.
    echo Options:
    echo   -advanced     Use advanced analysis with decompilation
    echo   -json         Output in JSON format
    echo   -verbose      Enable verbose output
    echo   -output FILE  Save report to file
    echo.
    echo Examples:
    echo   webview_check.bat app.apk
    echo   webview_check.bat app.apk -advanced
    echo   webview_check.bat app.apk -json -output report.json
    echo.
    exit /b 1
)

set APK=%1
set SCRIPT=check_webview.py
set ARGS=

REM Check if APK file exists
if not exist "%APK%" (
    echo Error: APK file not found: %APK%
    exit /b 1
)

REM Parse arguments
:parse_args
shift
if not "%1"=="" (
    if "%1"=="-advanced" (
        set SCRIPT=check_webview_advanced.py
    ) else if "%1"=="-json" (
        set ARGS=!ARGS! --json
    ) else if "%1"=="-verbose" (
        set ARGS=!ARGS! -v
    ) else if "%1"=="-output" (
        shift
        set ARGS=!ARGS! -o %1
    ) else (
        set ARGS=!ARGS! %1
    )
    goto parse_args
)

REM Run the script
echo.
echo Running WebView analysis with %SCRIPT%...
echo.

python "%SCRIPT%" "%APK%" !ARGS!

endlocal
