@echo off
echo ===================================
echo  Larranaga -- Backend (FastAPI)
echo ===================================
cd /d "%~dp0backend"

if not exist ".venv" (
    echo Creando entorno virtual...
    python -m venv .venv
)

call .venv\Scripts\activate

echo Instalando dependencias...
pip install -r requirements.txt -q

echo.
echo Iniciando servidor en http://localhost:8000
echo Documentacion en http://localhost:8000/docs
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

call deactivate
cd /d "%~dp0"
echo.
echo Backend detenido. Listo para volver a iniciar.
