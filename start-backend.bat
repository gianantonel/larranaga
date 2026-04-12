@echo off
echo ===================================
echo  Larranaga -- Backend (FastAPI)
echo ===================================
cd /d "%~dp0backend"

if not exist ".venv" (
    echo Creando entorno virtual...
    python -m venv .venv
)

echo Instalando dependencias...
.venv\Scripts\pip install -r requirements.txt -q

echo.
echo Iniciando servidor en http://localhost:8000
echo Documentacion en http://localhost:8000/docs
echo.
.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

cd /d "%~dp0"
echo.
echo Backend detenido. Listo para volver a iniciar.
