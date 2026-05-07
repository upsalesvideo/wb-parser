@echo off
title WB Parser
color 0D
cls
echo.
echo  ============================================
echo       WB Parser - Парсер Wildberries
echo  ============================================
echo.
echo  [1/3] Переходим в папку...
cd /d "%~dp0"

echo  [2/3] Запускаем сервер...
echo.

start "WB Parser Server" /min cmd /c "python app.py & pause"

echo  [3/3] Ждём запуска (3 сек)...
timeout /t 3 /nobreak > nul

echo  Открываем браузер...
start "" "http://localhost:5050"

echo.
echo  ============================================
echo   Готово! Браузер открыт.
echo   Это окно можно закрыть.
echo   Сервер работает в фоне (в отдельном окне).
echo  ============================================
echo.
pause
