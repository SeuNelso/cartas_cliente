FROM python:3.12.3-slim

WORKDIR /app

# Instalar fontes e dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    fonts-dejavu \
    fonts-liberation \
    fonts-freefont-ttf \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-mono \
    fonts-noto-color-emoji \
    fontconfig \
    wget \
    cabextract \
    && fc-cache -f -v \
    && rm -rf /var/lib/apt/lists/*

# Instalar Microsoft Fonts (Arial, etc.) - método alternativo
RUN echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections && \
    apt-get update && \
    apt-get install -y --no-install-recommends ttf-mscorefonts-installer && \
    fc-cache -f -v && \
    rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app.py .
COPY templates/ templates/

# Criar pastas necessárias
RUN mkdir -p uploads temp

# Verificar fontes instaladas
RUN fc-list | grep -i arial || echo "Arial não encontrada, usando fallback"

# Expor porta
EXPOSE 8080

# Comando de inicialização
CMD gunicorn app:app --bind 0.0.0.0:8080 --workers 1 --timeout 120 