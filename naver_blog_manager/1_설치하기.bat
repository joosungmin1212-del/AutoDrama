@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   PT샵 네이버 블로그 매니저 - 설치 (처음 1번만)
echo ============================================
echo.

rem "python" 명령이 있어 보여도 실제로는 마이크로소프트 스토어로 안내만 하는 가짜인 경우가
rem 아주 흔해서, 진짜로 코드를 실행할 수 있는지 직접 확인한다 (py 런처를 먼저 시도).
set PY=
py -c "import sys" >nul 2>nul
if not errorlevel 1 set PY=py

if not defined PY (
    python -c "import sys" >nul 2>nul
    if not errorlevel 1 set PY=python
)

if not defined PY (
    echo [!] 이 PC에서 정상적으로 동작하는 Python을 찾지 못했습니다.
    echo.
    echo     ※ 혹시 "python"이라고 입력했을 때 마이크로소프트 스토어 창이 열린 적이 있다면,
    echo        그건 진짜 설치가 아닙니다. 아래에서 정식 버전을 설치해주세요.
    echo.
    echo     1^) 자동으로 열리는 python.org 사이트에서 노란색 "Download Python" 버튼 클릭
    echo     2^) 설치 화면 맨 아래 "Add python.exe to PATH" 체크박스를 꼭 켜기
    echo     3^) 설치가 끝나면 이 파일을 다시 더블클릭해주세요.
    echo.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 프로그램 실행 환경을 만드는 중... (사용하는 Python 명령: %PY%)
%PY% -m venv .venv
if errorlevel 1 (
    echo.
    echo [!] 환경 만들기에 실패했습니다. 아마도 "%PY%"가 마이크로소프트 스토어의
    echo     가짜 파이썬 바로가기일 가능성이 높습니다. 아래 중 하나를 시도해주세요:
    echo.
    echo     - 설정 ^> 앱 ^> 고급 앱 설정 ^> 앱 실행 별칭 에서 python/python3 관련 항목을 꺼기
    echo     - 또는 python.org에서 정식 파이썬을 설치 (설치 시 "Add python.exe to PATH" 체크)
    echo.
    echo     조치 후 이 파일을 다시 더블클릭해주세요.
    start https://www.python.org/downloads/
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
