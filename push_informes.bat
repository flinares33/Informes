@echo off
chcp 65001 >nul
setlocal

set REPO=C:\Users\FranciscoLinares\Informes
set BASE=C:\Users\FranciscoLinares\OneDrive - Solusoft\Documents\2026\Claude\Dashboard Celulas

for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set HOY=%%a

set ORIGEN=%BASE%\%HOY%
set DESTINO=%REPO%\%HOY%

if not exist "%ORIGEN%" (
    echo [ERROR] No existe la carpeta de hoy: %ORIGEN%
    pause
    exit /b 1
)

if not exist "%DESTINO%" mkdir "%DESTINO%"

echo Copiando HTMLs...
xcopy /Y /Q "%ORIGEN%\*.html" "%DESTINO%\" >nul

cd /d "%REPO%"
git add .
git commit -m "Informes %HOY%"
git push

echo.
echo LISTO - Subido a GitHub
pause
