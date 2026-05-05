FROM python:3.11-slim

WORKDIR /app

# requirements primero para aprovechar cache de pip
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend code
COPY backend/ /app

# Módulo R-01 + R-02: vive afuera de backend/, lo necesita herramientas.py
# (Path en herramientas.py: parents[3] = / → /larranaga-accounting-agent)
COPY larranaga-accounting-agent/ /larranaga-accounting-agent

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
