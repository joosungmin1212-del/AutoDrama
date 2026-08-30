@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   PT샵 네이버 블로그 매니저 - 설치 (처음 1번만)
echo ============================================
echo.

call :find_python
if not defined PY (
    echo [1/5] 이 PC엔 Python이 없네요. 자동으로 설치를 시도할게요. ^(몇 분 걸릴 수 있어요^)
    call :auto_install_python
    call :find_python
)

if not defined PY (
    echo.
    echo [!] 자동 설치에 실패했습니다. 아래 방법으로 직접 설치해주세요.
    echo.
    echo     1^) 자동으로 열리는 python.org 사이트에서 노란색 "Download Python" 버튼 클릭
    echo     2^) 설치 화면 맨 아래 "Add python.exe to PATH" 체크박스를 꼭 켜기
    echo     3^) 설치가 끝나면 이 파일을 다시 더블클릭해주세요.
    echo.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [2/5] 프로그램 실행 환경을 만드는 중... ^(사용하는 Python: %PY%^)
%PY% -m venv .venv
if errorlevel 1 (
    echo.
    echo [!] 환경 만들기에 실패했습니다. 이 창의 내용을 캡처해서 문의해주세요.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo [3/5] 필요한 프로그램들을 설치하는 중... ^(인터넷 상황에 따라 몇 분 걸릴 수 있어요^)
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo [!] 설치 중 오류가 발생했습니다. 인터넷 연결을 확인하고 다시 실행해주세요.
    pause
    exit /b 1
)

echo [4/5] 네이버 로그인/글쓰기에 필요한 브라우저를 설치하는 중...
python -m playwright install chromium

echo [5/5] 설정 파일을 준비하는 중...
if not exist ".env" copy ".env.example" ".env" >nul

echo.
echo ============================================
echo   설치가 완료되었습니다!
echo   이제부터는 "2_실행하기.bat" 파일만 더블클릭하면 됩니다.
echo ============================================
echo.
pause
exit /b 0


:find_python
rem 진짜로 코드를 실행할 수 있는 Python을 찾는다.
rem (마이크로소프트 스토어로 안내만 하는 가짜 python.exe는 "where"에는 걸리지만
rem  실제로 실행하면 실패하므로, 반드시 코드를 돌려서 확인한다.)
set PY=
py -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set PY=py
    goto :eof
)
python -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set PY=python
    goto :eof
)
for /f "delims=" %%D in ('dir /b /ad /o-n "%LOCALAPPDATA%\Programs\Python\Python3*" 2^>nul') do (
    if not defined PY (
        if exist "%LOCALAPPDATA%\Programs\Python\%%D\python.exe" (
            "%LOCALAPPDATA%\Programs\Python\%%D\python.exe" -c "import sys" >nul 2>nul
            if not errorlevel 1 set "PY=%LOCALAPPDATA%\Programs\Python\%%D\python.exe"
        )
    )
)
goto :eof


:auto_install_python
where winget >nul 2>nul
if not errorlevel 1 (
    echo     - winget으로 자동 설치를 시도하는 중...
    winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements >nul 2>nul
)
call :find_python
if defined PY goto :eof

echo     - 설치파일을 직접 내려받는 중...
set "PYEXE=%TEMP%\python-installer.exe"
curl -fsSL -o "%PYEXE%" "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe" >nul 2>nul
if not exist "%PYEXE%" (
    echo     - 다운로드에 실패했습니다. ^(인터넷 연결을 확인해주세요^)
    goto :eof
)
echo     - 설치 중입니다... ^(화면에 별다른 표시가 없어도 정상입니다. 잠시만 기다려주세요^)
"%PYEXE%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
del "%PYEXE%" >nul 2>nul
goto :eof
