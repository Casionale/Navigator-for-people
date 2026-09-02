@echo off
rem ============================================================
rem  Запуск Flask-приложения «Navigator API» (booking.dop29.ru)
rem ============================================================
setlocal

rem --- Путь к проекту (папка, где лежит этот батник) ---
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

rem --- Венв проекта ---
set "PY=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [ОШИБКА] Не найден Python венв: %PY%
  pause
  exit /b 1
)

title Navigator API - http://127.0.0.1:5000

echo Starting Navigator API on http://127.0.0.1:5000 ...
echo Press Ctrl+C to stop.

rem --- Открыть браузер после короткой паузы ---
start "" /b cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000/login"

rem --- Запуск сервера ---
"%PY%" -m flask run --host 127.0.0.1 --port 5000

echo.
echo Server stopped.
pause
endlocal
