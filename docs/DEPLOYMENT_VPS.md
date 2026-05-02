# Deployment del Tunnel en el VPS de Hostinger

Esta guía describe los **pasos finales** para activar `larranaga.optimizar-ia.com`
una vez configurado todo en Cloudflare.

## Estado actual ✅

| Componente | Estado |
|-----------|--------|
| Cuenta Cloudflare | Creada (`Optimizar.ai@gmail.com`) |
| Dominio `optimizar-ia.com` | Activo en Cloudflare (NS apuntan a `aaron.ns` y `heather.ns`) |
| Tunnel `larranaga-prod` | Creado (ID: `5b1e9924-b418-4d84-8664-dfeb49557667`) |
| Public hostname | `larranaga.optimizar-ia.com` → `http://frontend:80` |
| Zero Trust team | `optimizar.cloudflareaccess.com` |
| Token | Guardado en `.env` raíz del proyecto (gitignored) |

## Información del VPS

```
Servidor: srv1127715.hstgr.cloud
IP:       72.61.52.206
Plan:     KVM 2 (Hostinger)
Vence:    2026-05-14
```

---

## 🚀 Pasos para deploy

### 1. SSH al VPS

```bash
ssh root@72.61.52.206
# (o el usuario que corresponda)
```

### 2. Clonar / actualizar el repo

```bash
# Si es la primera vez:
cd /opt
git clone https://github.com/optimizarai-del/larranaga.git
cd larranaga
git checkout fase-2

# Si ya está clonado:
cd /opt/larranaga
git fetch origin
git checkout fase-2
git pull origin fase-2
```

### 3. Crear `.env` con el token

Copiar el contenido del `.env` local (NO commiteado) al VPS:

```bash
cat > /opt/larranaga/.env << 'EOF'
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiNDE3NDBmZDhhNWYzMWFmYjNjNmVkZWNlYzAwOGQ2N2QiLCJ0IjoiNWIxZTk5MjQtYjQxOC00ZDg0LTg2NjQtZGZlYjQ5NTU3NjY3IiwicyI6Ik5EQTJOVEEyT1RJdE5tTTRaQzAwTm1RMUxUZzJNREV0Tm1JNVpUSXdaRGcxWVRnNCJ9
EOF

# Verificar permisos
chmod 600 /opt/larranaga/.env
```

### 4. Verificar que existe `backend/.env`

```bash
ls -l /opt/larranaga/backend/.env
# Si no existe, crearlo (con SECRET_KEY, ENCRYPTION_KEY, etc — usar el que ya tenga el VPS)
```

### 5. Build de las imágenes

```bash
cd /opt/larranaga
docker compose build
```

### 6. Levantar todo + tunnel

```bash
docker compose --profile tunnel up -d
```

### 7. Verificar que el tunnel está activo

```bash
docker compose logs cloudflared
```

Buscar en los logs:
```
INF Connection registered connIndex=0 location=eze01
INF Connection registered connIndex=1 location=eze01
```

Y en el dashboard de Cloudflare:
**Zero Trust → Networks → Connectors → larranaga-prod**
debe estar en estado **HEALTHY** (verde).

### 8. Probar la URL

Abrir en cualquier navegador: **https://larranaga.optimizar-ia.com**

Debería cargar la app de Larrañaga (login screen).

---

## 🛠️ Operación

### Logs

```bash
docker compose logs -f cloudflared        # Solo tunnel
docker compose logs -f frontend backend    # App
```

### Reiniciar solo el tunnel

```bash
docker compose restart cloudflared
```

### Bajar todo

```bash
docker compose --profile tunnel down
```

### Update (después de un git pull)

```bash
cd /opt/larranaga
git pull origin fase-2
docker compose --profile tunnel up -d --build
```

---

## 🛡️ Hardening recomendado (post-deploy)

Una vez funcionando, configurar en el dashboard:

1. **Cloudflare → Security → WAF** → activar:
   - Bot Fight Mode: ON
   - Browser Integrity Check: ON
   - Challenge Tor exit nodes: Managed Challenge

2. **Cloudflare → Security → Settings**:
   - Security Level: Medium
   - Challenge Passage: 30 minutes

3. **Cloudflare → SSL/TLS → Overview**:
   - Cambiar a **Full (strict)** una vez que el tunnel esté OK
   - Always Use HTTPS: ON

4. **Cloudflare → Rules → Rate Limiting Rules** (Free tier permite 1):
   - Crear regla: `/auth/login` → 5 reqs/min/IP
   - Acción: Block

5. **Cerrar puertos del VPS** que ya no se necesitan exponer públicamente:
   - El puerto 80 puede quedar cerrado en el firewall del VPS — el tunnel
     se conecta de salida, no necesita inbound.

---

## 🆘 Troubleshooting

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `502 Bad Gateway` | Frontend container caído | `docker compose ps`, `docker compose restart frontend` |
| Tunnel "Inactive" en dashboard | cloudflared no levantó | `docker compose logs cloudflared` y verificar token |
| `unable to reach origin service` en logs | URL mal configurada | Verificar Public Hostname URL = `http://frontend:80` |
| Subdominio no resuelve | DNS aún propagando | Esperar 5-10 min más, verificar en `dig larranaga.optimizar-ia.com` |
| Cert SSL inválido | Modo SSL/TLS = Off | Cloudflare → SSL/TLS → Overview → cambiar a Full |
