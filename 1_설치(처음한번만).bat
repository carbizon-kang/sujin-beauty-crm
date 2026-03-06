@echo off
chcp 65001 > nul
echo ================================
echo  수진뷰티 CRM - 최초 설치
echo ================================
echo.

:: Python 설치 여부 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo.
    echo https://www.python.org/downloads/ 에서
    echo Python을 설치한 후 다시 실행해주세요.
    echo.
    echo [중요] 설치 시 "Add Python to PATH" 반드시 체크!
    pause
    exit /b 1
)

echo Python 확인 완료!
echo.
echo 필요한 패키지를 설치합니다... (잠시 기다려주세요)
echo.

pip install -r requirements.txt

echo.
echo ================================
echo  설치 완료!
echo  이제 "2_실행.bat" 을 더블클릭하세요.
echo ================================
pause
