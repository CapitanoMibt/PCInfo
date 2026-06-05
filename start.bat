@echo off
set "DIR=%~dp0"

rem Создаём временный PS1-скрипт для фонового проигрывания
set "PSFILE=%TEMP%\play_sound_%RANDOM%.ps1"
(echo $p=(New-Object System.Media.SoundPlayer '%DIR%sounds\sound.wav'^)
echo $p.PlaySync(^)
) > "%PSFILE%"

rem Запускаем звук в отдельном скрытом процессе
start "" /B powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File "%PSFILE%"

rem Сразу запускаем Python
start "" "%DIR%PythonRUN.pyw"

rem Удаляем временный файл после проигрывания (с задержкой)
timeout /t 2 /nobreak >nul
del "%PSFILE%" 2>nul

exit
