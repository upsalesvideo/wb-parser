@echo off
title Остановка WB Parser
echo  Останавливаем WB Parser...
taskkill /f /im python.exe /fi "WINDOWTITLE eq WB Parser Server" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5050') do taskkill /f /pid %%a >nul 2>&1
echo  Сервер остановлен.
timeout /t 2 /nobreak > nul
