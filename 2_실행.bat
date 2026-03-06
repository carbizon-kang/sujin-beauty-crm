@echo off
chcp 65001 > nul
echo ================================
echo  수진뷰티 고객 관리 시스템 시작
echo ================================
echo.
echo 잠시 후 브라우저가 자동으로 열립니다.
echo 브라우저가 안 열리면 주소창에 입력: http://localhost:8501
echo.
echo [종료하려면 이 창을 닫거나 Ctrl+C 를 누르세요]
echo.

cd /d "%~dp0"

:: 내 컴퓨터 IP 자동으로 찾아서 표시
echo 핸드폰에서 접속할 주소:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP: =%
echo   http://%IP%:8501
echo.
echo (위 주소를 핸드폰 브라우저에 입력하세요 - 같은 와이파이여야 합니다)
echo.

python -m streamlit run app.py --server.address 0.0.0.0 --server.headless false
pause
