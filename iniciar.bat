@echo off
chcp 65001 >nul
title DiagnosticoPro - Lanzador
cd /d "%~dp0"

echo ============================================
echo    DiagnosticoPro - Diagnostico Automotriz
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
    echo Descarga Python 3.10+ desde: https://www.python.org/downloads/
    echo IMPORTANTE: marca "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)
echo [OK] Usando lanzador: %PYLAUNCHER%

REM --- Crear entorno virtual si no existe ---
if not exist "venv\Scripts\python.exe" (
    echo [1/3] Creando entorno virtual por primera vez...
    %PYLAUNCHER% -m venv venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo       Entorno virtual creado.
    echo.
    echo [2/3] Instalando dependencias (esto tarda unos minutos)...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip >nul 2>&1
    pip install -r requirements-pc.txt
    if errorlevel 1 (
        echo [ERROR] Fallo la instalacion de dependencias.
        pause
        exit /b 1
    )
    echo       Dependencias instaladas.
) else (
    echo [1/2] Entorno virtual encontrado.
    call venv\Scripts\activate.bat
    REM Verificar que las dependencias clave esten presentes
    python -c "import kivy, kivymd, serial" >nul 2>&1
    if errorlevel 1 (
        echo [2/2] Faltan dependencias, instalando...
        pip install -r requirements-pc.txt
    )
)

echo.
echo [OK] Iniciando DiagnosticoPro...
echo.

REM Dentro del venv 'python' ya apunta al interprete correcto
python run.py

if errorlevel 1 (
    echo.
    echo [ERROR] La aplicacion termino con un error.
    pause
)
