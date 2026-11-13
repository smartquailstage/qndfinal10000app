FROM python:3.11-slim
LABEL maintainer="support@smartquail.io"

# -----------------------------
# Argumentos y Variables de entorno dinámicas
# -----------------------------
ARG PROJECT_NAME=qnd04111app
ARG APP_NAME=sba
ARG APP_USER=appuser
ARG APP_VERSION=111

ENV PYTHONUNBUFFERED=1
ENV PROJECT_NAME=${PROJECT_NAME}
ENV APP_NAME=${APP_NAME}
ENV APP_USER=${APP_USER}
ENV APP_VERSION=${APP_VERSION}

# -----------------------------
# Dependencias del sistema
# -----------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libc6-dev \
    python3-dev \
    libpcre2-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    libffi-dev \
    gettext \
    curl \
    git \
    ca-certificates \
    fonts-dejavu-core \
    fonts-liberation \
    fonts-noto \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Copiar el proyecto al directorio de trabajo dinámico
# -----------------------------
WORKDIR /${PROJECT_NAME}
COPY . /${PROJECT_NAME}/

# -----------------------------
# Virtualenv + dependencias Python
# -----------------------------
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip setuptools wheel && \
    if [ -f "requirements.txt" ]; then /py/bin/pip install -r requirements.txt; \
    elif [ -f "pk.txt" ]; then /py/bin/pip install -r pk.txt; fi

# -----------------------------
# Crear usuario no-root seguro
# -----------------------------
RUN useradd --no-create-home --shell /usr/sbin/nologin ${APP_USER}

# -----------------------------
# Carpetas necesarias (incluyendo scripts) y permisos
# -----------------------------
RUN mkdir -p \
        static \
        media \
        staticfiles \
        scripts \
        /var/log/gunicorn \
    && chown -R ${APP_USER}:${APP_USER} \
        static \
        media \
        staticfiles \
        scripts \
        /var/log/gunicorn \
        /${PROJECT_NAME}

# -----------------------------
# Copiar init.sh explícitamente a su carpeta y dar permisos
# -----------------------------
COPY scripts/init.sh /${PROJECT_NAME}/scripts/init.sh
RUN chmod +x /${PROJECT_NAME}/scripts/init.sh

# -----------------------------
# PATH
# -----------------------------
ENV PATH="/py/bin:/${PROJECT_NAME}/scripts:$PATH"

# -----------------------------
# Usuario final
# -----------------------------
USER ${APP_USER}

# -----------------------------
# Puerto
# -----------------------------
EXPOSE 8000

# -----------------------------
# Comando de inicio
# -----------------------------
CMD ["init.sh"]