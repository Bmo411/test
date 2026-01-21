@echo off
SETLOCAL

REM Define ruta absoluta al proyecto
SET PROJECT_DIR=%~dp0

REM Ir al directorio del proyecto
cd /d %PROJECT_DIR%

REM Crear entorno virtual si no existe
IF NOT EXIST venv (
    python -m venv venv
)

REM Activar el entorno virtual
call venv\Scripts\activate

REM Instalar dependencias
pip install -r requirements.txt

REM Ejecutar la app Streamlit
streamlit run app.py

pause
