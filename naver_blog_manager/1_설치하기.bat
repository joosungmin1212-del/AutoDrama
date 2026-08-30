@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   PT샵 네이버 블로그 매니저 - 설치 (처음 1번만)
echo ============================================
echo.

set PY=python
where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        echo [!] 이 PC에 Python이 설치되어 있지 않습니다.
        echo.
        echo     1^) 아래 사이트가 자동으로 열립니다.
        echo     2^) 노란색 "Download Python" 버튼을 눌러 설치하세요.
        echo     3^) 설치 화면 맨 아래 "Add python.exe to PATH" 체크박스를 꼭 켜주세요!
        echo     4^) 설치가 끝나면 이 파일을 다시 더블클릭해주세요.
        echo.
        start https://www.python.org/downloads/
        pause
        exit /b 1
    )
    set PY=py
)

echo [1/4] 프로그램 실행 환경을 만드는 중...
%PY% -m venv .venv
if errorlevel 1 (
    echo [!] 환경 만들기에 실패했습니다. Python을 다시 설치해보시거나, 이 창의 내용을 캡처해서 문의해주세요.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo [2/4] 필요한 프로그램들을 설치하는 중... (인터넷 상황에 따라 몇 분 걸릴 수 있어요)
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo [!] 설치 중 오류가 발생했습니다. 인터넷 연결을 확인하고 다시 실행해주세요.
    pause
    exit /b 1
)

echo [3/4] 네이버 로그인/글쓰기에 필요한 브라우저를 설치하는 중...
python -m playwright install chromium

echo [4/4] 설정 파일을 준비하는 중...
if not exist ".env" copy ".env.example" ".env" >nul

echo.
echo ============================================
echo   설치가 완료되었습니다!
echo   이제부터는 "2_실행하기.bat" 파일만 더블클릭하면 됩니다.
echo ============================================
echo.
pause
