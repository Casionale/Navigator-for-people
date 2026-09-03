@echo off
rem ============================================================
rem  Деплой Flask-приложения «Navigator API» на хост e621-love
rem  (PuTTY сессия "pony", удалённая директория /home/e621/navigator)
rem ============================================================
setlocal

rem --- Путь к проекту (папка, где лежит этот батник) ---
set "APP_DIR=%~dp0"

rem --- Пути к PuTTY утилитам ---
set "PSCP=C:\Program Files\PuTTY\pscp.exe"
set "PLINK=C:\Program Files\PuTTY\plink.exe"

rem --- Сессия PuTTY и удалённая директория приложения ---
set "SESSION=pony"
set "REMOTE_DIR=/home/e621/navigator"

rem --- Имя systemd-сервиса ---
set "SERVICE=navigator.service"

if not exist "%PSCP%" (
  echo [ОШИБКА] Не найден pscp: %PSCP%
  pause
  exit /b 1
)
if not exist "%PLINK%" (
  echo [ОШИБКА] Не найден plink: %PLINK%
  pause
  exit /b 1
)

echo ============================================================
echo  Деплой Navigator API (web_version) на e621-love
echo  Локально:  %APP_DIR%
echo  Удалённо:  %REMOTE_DIR%
echo ============================================================
echo.

rem --- 1. Загрузка файлов приложения (кроме __pycache__) ---
echo [1/3] Копирую файлы на сервер...
"%PSCP%" -load %SESSION% -r "%APP_DIR%app.py" "%APP_DIR%navigator.py" "%APP_DIR%requirements.txt" "%APP_DIR%CHANGELOG.md" "%APP_DIR%.github_token" e621@bakasenpai.ru:%REMOTE_DIR%/
if errorlevel 1 goto :error

"%PSCP%" -load %SESSION% -r "%APP_DIR%templates" e621@bakasenpai.ru:%REMOTE_DIR%/
if errorlevel 1 goto :error

"%PSCP%" -load %SESSION% -r "%APP_DIR%static" e621@bakasenpai.ru:%REMOTE_DIR%/
if errorlevel 1 goto :error

rem --- 2. Проверка перезагрузки сервиса ---
echo.
echo [2/3] Перезапускаю сервис %SERVICE% ...
"%PLINK%" -load %SESSION% -batch "sudo systemctl restart %SERVICE% || systemctl restart %SERVICE%"
if errorlevel 1 goto :error

rem --- 3. Проверка статуса сервиса ---
echo.
echo [3/3] Статус сервиса:
"%PLINK%" -load %SESSION% -batch "systemctl is-active %SERVICE%; systemctl --no-pager status %SERVICE% | head -n 8"

echo.
echo ============================================================
echo  Деплой завершён.
echo ============================================================
pause
endlocal
exit /b 0

:error
echo.
echo [ОШИБКА] Деплой прерван.
pause
endlocal
exit /b 1
