@echo off
REM ─────────────────────────────────────────────────────────────────────────
REM Cloudflare Tunnel — Larranaga
REM
REM Levanta solo el tunnel (asume que backend y frontend ya estan corriendo
REM en local en los puertos por defecto: 8000 y 80).
REM
REM Uso:
REM   1. Crear .env en la raiz con CLOUDFLARE_TUNNEL_TOKEN=...
REM   2. Doble click en este archivo
REM
REM Requiere docker (mas simple) o cloudflared.exe instalado.
REM ─────────────────────────────────────────────────────────────────────────

echo ========================================
echo  Cloudflare Tunnel - Larranaga
echo ========================================
echo.

REM Verificar que existe .env
if not exist "%~dp0.env" (
    echo ERROR: No se encuentra el archivo .env en la raiz del proyecto.
    echo.
    echo Crear copiando el ejemplo:
    echo    copy .env.example .env
    echo.
    echo Y luego editar .env y pegar el token de Cloudflare:
    echo    CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoi...
    echo.
    pause
    exit /b 1
)

REM Verificar Docker
where docker >nul 2>&1
if %errorlevel% equ 0 (
    echo [Docker detectado] Levantando tunnel via docker compose...
    cd /d "%~dp0"
    docker compose --profile tunnel up -d cloudflared
    echo.
    echo Tunnel levantado. Ver logs con:
    echo    docker compose logs -f cloudflared
    echo.
    pause
    exit /b 0
)

REM Si no hay Docker, intentar con cloudflared.exe
where cloudflared >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Ni Docker ni cloudflared.exe estan instalados.
    echo.
    echo Opciones:
    echo   1. Instalar Docker Desktop:   https://www.docker.com/products/docker-desktop/
    echo   2. Instalar cloudflared:      https://github.com/cloudflare/cloudflared/releases
    echo.
    pause
    exit /b 1
)

REM Cargar token desde .env
for /f "usebackq tokens=1,2 delims==" %%A in ("%~dp0.env") do (
    if "%%A"=="CLOUDFLARE_TUNNEL_TOKEN" set TOKEN=%%B
)

if "%TOKEN%"=="" (
    echo ERROR: CLOUDFLARE_TUNNEL_TOKEN no esta seteado en .env
    pause
    exit /b 1
)

echo [cloudflared.exe detectado] Levantando tunnel...
cloudflared tunnel --no-autoupdate run --token %TOKEN%
