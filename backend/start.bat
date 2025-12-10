@echo off
REM Скрипт запуска backend для Windows
echo Запуск Astra Linux Training Simulator Backend...

REM Активация виртуального окружения
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Ошибка: виртуальное окружение не найдено
    echo Создайте его командой: python -m venv venv
    pause
    exit /b 1
)

REM Запуск приложения
python run.py

pause

