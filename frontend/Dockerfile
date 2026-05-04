# ── Etapa 1: build de React ───────────────────────────────────────────────────
FROM node:18-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# ── Etapa 2: nginx sirve el build + proxea /api al backend ────────────────────
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Template del nginx con $BACKEND_URL para envsubst al startup
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# BACKEND_URL puede sobreescribirse por env var. Default = service name "backend"
# para mantener compatibilidad con docker-compose viejo
ENV BACKEND_URL=http://backend:8000/

EXPOSE 80
