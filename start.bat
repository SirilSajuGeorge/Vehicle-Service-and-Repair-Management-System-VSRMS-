@echo off
setlocal

echo 🚗 Starting VSRMS (Vehicle Service ^& Repair Management System)
echo ==================================================

REM Check if Docker is installed
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    echo    Visit: https://docs.docker.com/desktop/windows/
    pause
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker Compose is not available. Please ensure Docker Desktop is running.
    pause
    exit /b 1
)

REM Check if Docker daemon is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker daemon is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo ✅ Docker is installed and running

REM Create instance directory if it doesn't exist
if not exist "instance" mkdir instance
echo ✅ Created instance directory for database

REM Build and start the application
echo 🔧 Building and starting VSRMS...
docker-compose up --build -d

REM Wait a moment for the application to start
echo ⏳ Waiting for application to start...
timeout /t 10 /nobreak >nul

REM Check if the application is running
docker-compose ps | findstr "Up" >nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ VSRMS is running successfully!
) else (
    echo ❌ VSRMS failed to start. Check logs with: docker-compose logs
    pause
    exit /b 1
)

echo.
echo 🎉 VSRMS is now ready!
echo ==================================================
echo 🌐 Access the application at: http://localhost:5000
echo 👨‍💼 Admin Login:
echo    📧 Email:    admin@vsrms.com
echo    🔐 Password: admin123
echo.
echo 📝 Useful Commands:
echo    🔍 View logs:        docker-compose logs -f
echo    ⏹️  Stop service:     docker-compose down
echo    🔄 Restart service:  docker-compose restart
echo    📊 Check status:     docker-compose ps
echo.
echo ⚠️  IMPORTANT: Change the default admin password after first login!
echo ==================================================
pause
