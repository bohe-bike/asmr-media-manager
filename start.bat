@echo off
setlocal

echo ==========================================
echo   ASMR Media Manager
echo ==========================================
echo.
echo   1 Install dependencies
echo   2 Dev mode (backend + frontend)
echo   3 Backend only
echo   4 Frontend only
echo   5 Docker mode
echo.
set /p choice="Select [1-5]: "

if "%choice%"=="1" goto install
if "%choice%"=="2" goto dev
if "%choice%"=="3" goto backend
if "%choice%"=="4" goto frontend
if "%choice%"=="5" goto docker
echo Invalid option
goto end

:install
echo.
echo [1/2] Install backend dependencies...
cd /d "%~dp0backend"
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo Backend done.
echo.
echo [2/2] Install frontend dependencies...
cd /d "%~dp0frontend"
call npm install
echo Frontend done.
echo.
echo All installed. Run option 2 to start.
goto end

:dev
echo.
echo Starting backend...
cd /d "%~dp0backend"
start "ASMR-Backend" cmd /k "venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 0.0.0.0 --port 8080"
echo Starting frontend...
cd /d "%~dp0frontend"
start "ASMR-Frontend" cmd /k "npm run dev"
echo.
echo Backend: http://localhost:8080/docs
echo Frontend: http://localhost:5173
goto end

:backend
cd /d "%~dp0backend"
call venv\Scripts\activate.bat
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
goto end

:frontend
cd /d "%~dp0frontend"
call npm run dev
goto end

:docker
cd /d "%~dp0"
docker compose up -d
echo.
echo Visit: http://localhost:3000
goto end

:end
pause
