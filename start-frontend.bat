@echo off
echo ===================================
echo  Larrañaga — Frontend (React/Vite)
echo ===================================
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo Instalando dependencias npm...
    npm install
)

echo.
echo Iniciando servidor en http://localhost:5173
echo.
npm run dev
