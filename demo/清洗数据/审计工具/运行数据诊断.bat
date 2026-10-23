@echo off
chcp 65001 >nul
setlocal
set "DATA_FILE=C:\Users\13067\Desktop\论文\非洲\demo\清洗数据\清洗数据.json"
set "SCRIPT=%~dp0africa_audit.py"
set "OUT_DIR=C:\Users\13067\Desktop\论文\非洲\demo\非洲_诊断输出"
if not exist "%DATA_FILE%" (
    echo ERROR: Cannot find JSON data at "%DATA_FILE%"
    pause
    exit /b 1
)
if not exist "%SCRIPT%" (
    echo ERROR: Cannot find script "%SCRIPT%"
    pause
    exit /b 1
)
py -3 "%SCRIPT%" --input "%DATA_FILE%" --output "%OUT_DIR%"
if errorlevel 1 (
    echo ERROR: Audit failed. Please send a screenshot of the error.
) else (
    echo Upload the resulting ZIP in: %OUT_DIR%
)
pause
