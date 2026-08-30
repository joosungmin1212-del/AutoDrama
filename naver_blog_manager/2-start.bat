@echo off
chcp 65001 >nul
cd /d "%~dp0"
title PT샵 네이버 블로그 매니저

if not exist ".venv\Scripts\activate.bat" (
    echo [!] 아직 설치가 안 되어 있습니다. "1-install.bat"을 먼저 더블클릭해주세요.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

rem 설치가 중간에 끊겼거나 일부만 됐을 수 있으니, 실행 전에 핵심 패키지가 다 있는지 확인하고
rem 없으면 조용히 다시 설치를 시도한다 (매번 확인만 하는 거라 이미 다 있으면 순식간에 끝난다).
python -c "import fastapi, uvicorn, sqlalchemy, playwright, openai, cryptography" >nul 2>nul
if errorlevel 1 (
    echo [!] 설치가 완전히 끝나지 않은 것 같습니다. 부족한 부분을 다시 설치할게요...
    pip install --quiet -r requirements.txt
    python -c "import fastapi, uvicorn, sqlalchemy, playwright, openai, cryptography" >nul 2>nul
    if errorlevel 1 (
        echo.
        echo [!] 자동 복구에 실패했습니다. "1-install.bat"을 다시 실행해주세요.
        pause
        exit /b 1
    )
    echo     복구되었습니다.
    echo.
)

echo ============================================
echo   서버를 시작합니다. 잠시 후 브라우저가 자동으로 열립니다.
echo   (이 검은 창을 닫으면 프로그램이 꺼집니다. 켜둔 채로 사용하세요)
echo ============================================
echo.

python run.py

echo.
echo 프로그램이 종료되었습니다.
pause
