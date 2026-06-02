@echo off
chcp 65001 >nul
title DiagnosticoPro - Instalacion
cd /d "%~dp0"

echo ============================================
echo    DiagnosticoPro - Instalacion inicial
echo ============================================
echo.

REM --- Detectar el lanzador de Python (py preferente, luego python) ---
set PYLAUNCHER=
py --version >nul 2>&1
if not errorlevel 1 (
    set PYLAUNCHER=py
) else (
    python --version >nul 2>&1
    if not errorlevel 1 set PYLAUNCHER=python
)

if "%PYLAUNCHER%"=="" (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo.
    echo 1. Descarga Python 3.10 o superior desde:
    echo    https://www.python.org/downloads/
    echo 2. Durante la instalacion, MARCA la casilla "Add Python to PATH".
    echo 3. Vuelve a ejecutar este instalador.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('%PYLAUNCHER% --version 2^>^&1') do echo [OK] Python %%i detectado.
echo.

REM --- Crear entorno virtual ---
if exist "venv\Scripts\python.exe" (
    echo [INFO] El entorno virtual ya existe. Se reutilizara.
) else (
    echo [1/2] Creando entorno virtual...
    %PYLAUNCHER% -m venv venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

REM --- Instalar dependencias ---
echo [2/2] Instalando dependencias...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements-pc.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Fallo la instalacion de dependencias.
    echo Revisa tu conexion a internet e intenta de nuevo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo    Instalacion completada con exito
echo ============================================
echo.
echo Para iniciar la aplicacion, ejecuta: iniciar.bat
echo (o haz doble clic en ese archivo)
echo.
pause
