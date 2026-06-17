# Cloudflare Tunnel — Guía de configuración

Esta guía explica cómo conectar el proyecto Larrañaga a un dominio de Optimizar
usando Cloudflare Tunnel (gratis, sin abrir puertos en el router/VPS).

## ¿Por qué Cloudflare Tunnel?

| Beneficio | Detalle |
|-----------|---------|
| **DDoS gratis** | Cloudflare absorbe ataques antes de que lleguen al servidor |
| **HTTPS automático** | Certificado SSL/TLS gestionado por Cloudflare |
| **IP oculta** | El VPS nunca expone su IP pública |
| **Sin abrir puertos** | El túnel es saliente — no requiere configuración de firewall/router |
| **WAF + bot management** | Reglas anti-spam y bots maliciosos en el plan free |
| **Zero Trust opcional** | Login con email/SSO antes de llegar a la app (futuro) |

---

## 📋 Prerequisitos

- Dominio registrado a nombre de Optimizar (ej: `optimizar.ai`).
- Acceso al panel del registrar del dominio (NIC.ar, Namecheap, etc.) para
  cambiar los nameservers a los de Cloudflare.
- Servidor donde corre Larrañaga (VPS o local con Docker).

---

## 🚀 Setup paso a paso

### 1. Crear cuenta en Cloudflare

1. Entrar a https://dash.cloudflare.com/sign-up
2. Registrar con el mail de Optimizar (recomendado: usar un mail de equipo,
   no personal, así varias personas pueden gestionar la cuenta).
3. Verificar el mail.
4. Activar 2FA (Autenticación → Configuración del perfil → 2FA).

### 2. Agregar el dominio a Cloudflare

1. Dashboard → **Add a site** → escribir el dominio (ej: `optimizar.ai`).
2. Elegir plan **Free** ($0/mes — alcanza para Larrañaga).
3. Cloudflare escanea los DNS records existentes. Confirmar que están todos.
4. Copiar los **2 nameservers** que muestra Cloudflare (ej:
   `ana.ns.cloudflare.com` y `bob.ns.cloudflare.com`).
5. **Ir al registrar del dominio** (NIC.ar / Namecheap / etc.) y reemplazar
   los nameservers actuales por los de Cloudflare.
6. Volver al dashboard de Cloudflare y darle a **Done, check nameservers**.
   La propagación tarda entre 5 minutos y 24 horas (típicamente <1 hora).

> ⚠️ **Importante**: hasta que los nameservers no estén activos, el túnel
> no va a funcionar para resolver el subdominio. Verificar con
> `dig optimizar.ai NS` o https://www.whatsmydns.net/

### 3. Crear el Tunnel

1. Dashboard → **Zero Trust** (botón en el menú lateral).
2. Si es la primera vez en Zero Trust, te pide elegir un team name
   (ej: `optimizar`). El plan **Free** alcanza (50 usuarios).
3. **Networks** → **Tunnels** → **Create a tunnel**.
4. Tipo: **Cloudflared** (es el agente que vamos a correr).
5. Nombre del túnel: `larranaga-prod` (o como prefieras).
6. **Save tunnel**.
7. La pantalla siguiente muestra el comando para instalar cloudflared con
   un token. **Copiar solo el token** (la string larga después de `--token`).

### 4. Configurar el token en el proyecto

```bash
# En la raíz del proyecto larranaga-clean/
cp .env.example .env
# Editar .env y pegar el token:
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiNzg...
```

> 🔒 El archivo `.env` está en `.gitignore` — nunca se commitea.

### 5. Configurar las "Public Hostnames" del túnel

Acá decidís qué subdominios apuntan a qué servicios.

**Recomendado para Larrañaga:**

| Subdominio | Service | Notas |
|-----------|---------|-------|
| `larranaga.optimizar.ai` | `http://frontend:80` | App principal |

(opcional para el futuro)

| `api.larranaga.optimizar.ai` | `http://backend:8000` | Acceso directo a la API |
| `staging.larranaga.optimizar.ai` | otro tunnel | Entorno de staging |

**Pasos:**

1. Volver a **Zero Trust → Networks → Tunnels → larranaga-prod**.
2. Tab **Public Hostnames** → **Add a public hostname**.
3. Completar:
   - **Subdomain**: `larranaga`
   - **Domain**: elegir `optimizar.ai` del dropdown
   - **Path**: dejar vacío
   - **Service Type**: `HTTP`
   - **URL**: `frontend:80` (nombre del servicio en docker-compose)
4. **Save hostname**.

Cloudflare crea automáticamente un CNAME `larranaga.optimizar.ai` →
`<tunnel-id>.cfargotunnel.com`. No hace falta configurar DNS manualmente.

### 6. Levantar el túnel

```bash
# Desde la raíz del proyecto
docker compose --profile tunnel up -d

# Verificar logs
docker compose logs -f cloudflared
```

Buscar en los logs algo como:
```
INF Connection registered connIndex=0 location=eze01
INF Connection registered connIndex=1 location=eze01
```

✅ Listo. Acceder en https://larranaga.optimizar.ai

---

## 🛠️ Operación

### Comandos comunes

```bash
# Solo backend + frontend (sin túnel — para testing local)
docker compose up -d

# + túnel (producción)
docker compose --profile tunnel up -d

# Reiniciar solo el túnel (ej: tras cambiar token)
docker compose restart cloudflared

# Ver logs del túnel
docker compose logs -f cloudflared

# Bajar todo
docker compose --profile tunnel down
```

### Cambiar el token (rotación)

Si por seguridad necesitás rotar el token:

1. Zero Trust → Tunnel → Configure → **Refresh token**.
2. Pegar el nuevo en `.env`.
3. `docker compose restart cloudflared`.

### Apagar el túnel temporalmente

```bash
docker compose stop cloudflared
```

El túnel queda en estado "Inactive" en el dashboard. La app deja de ser
accesible vía Cloudflare; el VPS queda intacto.

---

## 🔐 Configuración de seguridad recomendada

Una vez que el túnel está corriendo, aplicar estas reglas en
**Security → WAF**:

| Regla | Acción | Detalle |
|-------|--------|---------|
| **Bot Fight Mode** | ON | Bloquea bots conocidos automáticamente |
| **Browser Integrity Check** | ON | Verifica que el cliente sea un browser real |
| **Challenge** Tor exit nodes | Managed Challenge | Filtra tráfico Tor (alto ratio de abuso) |
| **Rate Limiting**: `/auth/login` | 5 reqs/min/IP | Anti-brute-force |
| **Rate Limiting**: `/auth/register` | 1 req/hora/IP | Anti-spam de cuentas |

Para configurar reglas custom: **Security → WAF → Custom rules → Create rule**.

---

## 🆘 Troubleshooting

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| `502 Bad Gateway` desde el subdominio | El servicio interno está caído | `docker compose ps` y verificar `frontend` |
| `Tunnel not registered` en logs | Token inválido o roto | Refresh token en dashboard y actualizar `.env` |
| El subdominio no resuelve (DNS) | Nameservers no propagados aún | Esperar hasta 24h o verificar en whatsmydns.net |
| `connection refused` desde cloudflared | Service URL mal escrito | En Public Hostname usar `frontend:80` (sin `http://`) |
| `cloudflared` se reinicia en loop | `.env` faltante o token vacío | `cat .env` debe tener `CLOUDFLARE_TUNNEL_TOKEN=eyJ...` |

---

## 📚 Referencias

- [Cloudflare Tunnel docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- [Cloudflare Plans](https://www.cloudflare.com/plans/) (Free es suficiente)
- [Zero Trust Free tier](https://www.cloudflare.com/teams-pricing/) (50 users, 24 apps)
