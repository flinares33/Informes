@echo off
chcp 65001 >nul
echo ================================================================
echo  Registrar tarea: Generar Dashboards de Tickets - 6:00 PM diario
echo ================================================================
echo.

:: Verificar que se ejecuta como administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ejecuta este archivo como Administrador.
    echo Clic derecho ^> Ejecutar como administrador
    pause
    exit /b 1
)

set SCRIPT=C:\Users\FranciscoLinares\Informes\check_and_generate.ps1
set TASK_NAME=Solusoft_Dashboards_Tickets

:: Eliminar la tarea si ya existe
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: Crear la tarea: todos los días a las 18:00, usuario actual, PowerShell
schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "powershell.exe -NonInteractive -ExecutionPolicy Bypass -File \"%SCRIPT%\"" ^
  /sc daily ^
  /st 18:00 ^
  /ru "%USERNAME%" ^
  /rl HIGHEST ^
  /f

if %errorlevel% equ 0 (
    echo.
    echo [OK] Tarea "%TASK_NAME%" registrada correctamente.
    echo      Se ejecutara todos los dias a las 6:00 PM.
    echo.
    echo Para verificarla: Administrador de tareas ^> Biblioteca ^> %TASK_NAME%
) else (
    echo.
    echo [ERROR] No se pudo registrar la tarea. Codigo: %errorlevel%
)

pause
