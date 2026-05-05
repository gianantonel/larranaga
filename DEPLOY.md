# Despliegue de Larrañaga

Esta plataforma se despliega en Hostinger VPS (KVM 2, srv1127715) bajo el dominio público
`https://larranaga.optimizar-ia.com`. La arquitectura combina **EasyPanel** (servicios
backend y frontend con auto-deploy desde GitHub) y **Docker Compose** (cloudflared, que
está fuera de EasyPanel por una limitación técnica de la imagen oficial — ver más abajo).

---

## Arquitectura en producción

```
Internet (HTTPS)
    │
    ▼
Cloudflare Edge (CDN, WAF, DDoS)
    │
    ▼ Cloudflare Tunnel (cifrado, sin IP pública expuesta)
    │
cloudflared           ── /opt/larranaga/docker-compose.yml
    │                    en red Docker overlay easypanel-n8n_nuevo
    ▼
larranaga-frontend     ── EasyPanel (proyecto n8n_nuevo)
  nginx:alpine            sirve build de Vite + proxy /api/* al backend
    │ proxy /api/*
    ▼
larranaga-backend      ── EasyPanel (proyecto n8n_nuevo)
  Python 3.11 + FastAPI   /api/* (auth, clients, tasks, iva, insforge, etc.)
    │
    ▼
SQLite                 ── volume persistente larranaga-db en /app/dbfiles
```

---

## Workflow GitHub → EasyPanel

EasyPanel está conectado al repo `gianantonel/larranaga` y pulleea automáticamente la
rama configurada (actualmente `main`). El flujo es:

1. **Editás código local** en cualquier rama (`fase-2`, `fase-3`, etc.).
2. **PR → `main`** y mergeás cuando esté listo.
3. **EasyPanel detecta el push** y rebuildea la imagen del servicio afectado:
   - `larranaga-backend` rebuildea si tocaste `backend/`
   - `larranaga-frontend` rebuildea si tocaste `frontend/`
4. **El nuevo container reemplaza al viejo** sin downtime perceptible (~10s con cache de
   capas, ~60s con `--no-cache`).

> ⚠️ **Importante:** las features de fase 2 y fase 3 viven en sus respectivas ramas
> (`fase-2`, `fase-3`). Sólo lo que esté en `main` se despliega en producción.

### Estructura de ramas

| Rama | Contenido | Deploy |
|---|---|---|
| `main` | Fase 1 + InsForge | ✅ producción |
| `fase-2` | `main` + Tesorería, Liquidaciones, R-09 Maestro Proveedores, R-10 HWCRARCA, billetes, pagos, imputación, honorarios, profesionales | sin deploy |
| `fase-3` | `fase-2` + R-15 conciliación bancaria + frontend nginx templated | sin deploy |
| `dev` | espejo de `main` (rama de integración pre-PR) | sin deploy |

---

## Variables de entorno en EasyPanel

Las env vars se configuran en el **tab "Entorno"** de cada servicio. Para agregar/cambiar:

1. https://72.61.52.206:3000 → proyecto `n8n_nuevo` → servicio (`larranaga-backend` o
   `larranaga-frontend`).
2. Tab **Entorno** → editar el textarea con formato `KEY=value` (una por línea).
3. **Guardar** → **Implementar** (el container se recrea).

### Backend (`larranaga-backend`)

```
SECRET_KEY=<32-byte random hex — usado para firmar JWT>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
ENCRYPTION_KEY=<32-byte Fernet key — usado para cifrar clave_fiscal>
DATABASE_URL=sqlite:////app/dbfiles/larranaga.db
INSFORGE_API_KEY=ik_6e043a410661a9bfaed032bf81e065fd
INSFORGE_API_URL=https://vivnx98a.us-east.insforge.app
```

> ⚠️ `SECRET_KEY` y `ENCRYPTION_KEY` no se pueden rotar sin perder los JWT y las
> credenciales fiscales cifradas existentes. Si las cambiás, todos los usuarios se
> deben loguear de nuevo y las claves fiscales hay que re-ingresarlas.

### Frontend (`larranaga-frontend`)

```
BACKEND_URL=http://larranaga-backend:8000/
```

`nginx.conf.template` usa esta variable como `proxy_pass` del location `/api/*`. Por
defecto vale `http://backend:8000/` para mantener compatibilidad con el docker-compose
viejo, pero en EasyPanel hay que apuntarla al nombre del servicio.

---

## Cloudflared (fuera de EasyPanel)

`cloudflared` corre como un servicio Docker Compose en `/opt/larranaga/docker-compose.yml`
porque su **imagen oficial es distroless** (no tiene `/bin/sh`) y EasyPanel envuelve los
comandos en `sh -c`, lo que rompe el container.

### Configuración actual

```yaml
# /opt/larranaga/docker-compose.yml
services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    restart: unless-stopped
    command: tunnel --no-autoupdate run --token ${CLOUDFLARE_TUNNEL_TOKEN}
    env_file:
      - ./.env
    networks:
      - easypanel-n8n_nuevo

networks:
  easypanel-n8n_nuevo:
    external: true
```

### Cambiar el túnel apunte a otro servicio

1. https://one.dash.cloudflare.com → **Networks → Connectors** → `larranaga-prod`
2. Tab **Published application routes** → editar la entrada de `larranaga.optimizar-ia.com`
3. Cambiar el campo **Service URL** al nuevo destino (ejemplo: `larranaga-frontend:80`,
   `staging-frontend:80`, etc.)
4. **Save** — el cambio se aplica en segundos sin reiniciar nada.

### Cambiar el token de cloudflared

```bash
ssh root@72.61.52.206
cd /opt/larranaga
nano .env                            # editar CLOUDFLARE_TUNNEL_TOKEN=...
docker compose up -d --force-recreate cloudflared
```

### Logs del túnel

```bash
docker logs -f larranaga-cloudflared-1
```

---

## Cómo agregar un nuevo servicio en EasyPanel

Si necesitás un servicio adicional (ej. Redis, otro microservicio):

1. EasyPanel → proyecto `n8n_nuevo` → **+ Servicio**
2. Elegir tipo (App, Postgres, MySQL, Redis, etc.)
3. Configurar **Fuente** (GitHub repo o Imagen Docker)
4. Configurar **Entorno** con env vars necesarias
5. Configurar **Almacenamiento** si necesita volumes persistentes
6. **Implementar**

El servicio nuevo automáticamente queda en la red `easypanel-n8n_nuevo` y es resoluble
por DNS interno con su nombre (sin prefijo del proyecto).

---

## Procedimientos de operación

### Ver estado de los servicios

```bash
ssh root@72.61.52.206
docker ps --format 'table {{.Names}}\t{{.Status}}'
```

### Reiniciar un servicio

EasyPanel UI: tab del servicio → ícono de **reiniciar** (🔄) en la barra superior.

O desde terminal:

```bash
docker service update --force n8n_nuevo_larranaga-backend
```

### Hacer rollback de un deploy

EasyPanel guarda historial de implementaciones. Tab **Implementaciones** del servicio →
cualquier deploy verde tiene un botón para re-aplicar.

Alternativa via Git:

```bash
git revert <hash-del-commit-malo>
git push origin main          # EasyPanel auto-deploya
```

### Backup de la base de datos

```bash
ssh root@72.61.52.206
docker run --rm -v larranaga-db:/data -v /tmp:/backup alpine \
  tar czf /backup/larranaga-db-$(date +%F).tar.gz -C /data .
scp root@72.61.52.206:/tmp/larranaga-db-*.tar.gz ./
```

### Ejecutar comandos dentro del container

EasyPanel UI: tab del servicio → ícono **Console** (`>_`) → elegir Bash.

O desde terminal:

```bash
docker exec -it $(docker ps -q --filter 'name=larranaga-backend') bash
```

---

## Sincronización con InsForge

Larrañaga tiene 6 endpoints admin-only para sincronización con InsForge Cloud:

| Método | Path | Función |
|---|---|---|
| GET | `/api/insforge/status` | Estado conectividad + última sync |
| GET | `/api/insforge/test-read?table=clients` | Lee InsForge sin escribir |
| POST | `/api/insforge/sync` | Push local → InsForge (síncrono) |
| POST | `/api/insforge/sync-background` | Push en background |
| POST | `/api/insforge/pull` | Pull InsForge → local (UPSERT por id/cuit/email) |
| GET | `/api/insforge/preview-sql` | Preview del SQL exportado |

Los endpoints requieren auth JWT con rol `super_admin` o `admin*`.

### Auto-sync periódico

El backend puede correr un push automático a InsForge cada N segundos. Se controla con
estas env vars:

```
INSFORGE_AUTOSYNC_INTERVAL_SECONDS=3600   # 0 o sin definir = deshabilitado
```

Cuando está habilitado, el backend dispara un `sync_to_insforge()` en background al
intervalo indicado, sin bloquear las requests HTTP. Recomendado: 3600 (1 hora).

---

## Troubleshooting

### El sitio devuelve 530 o 502

`cloudflared` no puede alcanzar el frontend. Verificar:

```bash
docker logs --tail 30 larranaga-cloudflared-1
```

Si ves `Updated to new configuration`, el túnel está OK. Probá la conectividad
desde adentro de la red:

```bash
docker run --rm --network easypanel-n8n_nuevo alpine \
  wget -qO- http://larranaga-frontend:80/api/health
```

Debe devolver `{"status":"ok"}`.

### El backend crashea con `ModuleNotFoundError`

Falta una dependencia en `backend/requirements.txt`. Agregarla, push a `main`,
EasyPanel rebuildea.

### EasyPanel se queda colgado en "Recreating"

El container probablemente está en crash loop. Tab **Implementaciones** → `Ver` el
último deploy → mirar el error. Causas comunes:

- Comando incorrecto (recordar: EasyPanel envuelve en `sh -c`, no funciona con imágenes
  distroless como `cloudflare/cloudflared`)
- Env var faltante
- Conflicto de puerto en el host (no debería pasar — EasyPanel maneja red interna)

---

## Cambios futuros sugeridos

- [ ] Migrar `cloudflared` a EasyPanel cuando exista una imagen con shell o usemos un
      Dockerfile wrapper.
- [ ] Migrar a PostgreSQL cuando la BD crezca > 1 GB.
- [ ] Agregar healthchecks formales en EasyPanel para auto-restart si el backend cae.
- [ ] Setup de staging environment (subdominio aparte que apunta a `fase-2` o
      `fase-3`).
- [ ] CI/CD con tests automáticos antes de mergear PR a `main`.
