FROM python:3.11-slim-bookworm

# Configurações de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Instala dependências de sistema para libs Python nativas
# (WeasyPrint, Pillow, psycopg2, cairo, pango, OpenCV, XML, etc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpq-dev \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    libgl1 \
    libglib2.0-0 \
    libxml2-dev \
    libxslt-dev \
    shared-mime-info \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalação de dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY . .

# Detectar módulo WSGI automaticamente (busca wsgi.py em qualquer pasta)
RUN WSGI_MODULE="" && \
    WSGI_FILE=$(find . -maxdepth 2 -name "wsgi.py" -not -path "./venv/*" -not -path "./.venv/*" | head -1) && \
    if [ -n "$WSGI_FILE" ]; then \
    WSGI_DIR=$(dirname "$WSGI_FILE" | sed 's|^\./||' | tr '/' '.'); \
    WSGI_MODULE="${WSGI_DIR}.wsgi:application"; \
    fi && \
    if [ -z "$WSGI_MODULE" ]; then WSGI_MODULE="config.wsgi:application"; fi && \
    echo "export WSGI_MODULE=$WSGI_MODULE" > /app/.wsgi_config && \
    echo "[PYTHONJET] WSGI detectado: $WSGI_MODULE"

# Coleta de estáticos
RUN python manage.py collectstatic --noinput 2>/dev/null || true

# Configuração de porta e execução
ENV PORT=8080
EXPOSE 8080
CMD . /app/.wsgi_config && exec gunicorn $WSGI_MODULE --bind 0.0.0.0:${PORT:-8080} --timeout 0
