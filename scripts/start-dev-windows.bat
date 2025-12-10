@echo off
REM Скрипт запуска для разработки на Windows (без Podman)

echo 🚀 Запуск Astra Linux Training Simulator (режим разработки)

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не установлен
    exit /b 1
)

REM Проверка Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js не установлен
    exit /b 1
)

echo ✅ Зависимости проверены

REM Запуск backend в режиме разработки
echo.
echo 📦 Запуск backend (mock режим)...
cd backend
if not exist "venv" (
    echo Создание виртуального окружения...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -q -r requirements.txt

REM Установка переменной окружения для mock режима
set MOCK_SANDBOX=true
start "Backend API" cmd /k "venv\Scripts\activate.bat && set MOCK_SANDBOX=true && python run.py"

cd ..

REM Запуск frontend
echo.
echo 🌐 Запуск frontend...
cd frontend\web
if not exist "node_modules" (
    echo Установка зависимостей...
    call npm install
)

start "Frontend" cmd /k "npm start"

cd ..\..

echo.
echo ✅ Приложение запущено в режиме разработки!
echo    Backend:  http://localhost:8000 (mock режим - без реальных контейнеров)
echo    Frontend: http://localhost:3000
echo.
echo Для остановки закройте окна Backend и Frontend

pause

