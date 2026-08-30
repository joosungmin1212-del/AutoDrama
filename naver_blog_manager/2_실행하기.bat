@echo off
chcp 65001 >nul
cd /d "%~dp0"
title PT샵 네이버 블로그 매니저

if not exist ".venv\Scripts\activate.bat" (
    echo [!] 아직 설치가 안 되어 있습니다. "1_설치하기.bat"을 먼저 더블클릭해주세요.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo ============================================
echo   서버를 시작합니다. 잠시 후 브라우저가 자동으로 열립니다.
echo   (이 검은 창을 닫으면 프로그램이 꺼집니다. 켜둔 채로 사용하세요)
echo ============================================
echo.

start "" cmd /c "timeout /t 2 >nul && start http://127.0.0.1:8000"

python run.py

echo.
echo 프로그램이 종료되었습니다.
pause
