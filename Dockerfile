FROM python:3.13-slim

WORKDIR /app

# Instalar dependências do sistema necessárias para cairosvg
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar script de build e executar
COPY build.sh .
RUN chmod +x build.sh
RUN ./build.sh

# Copiar código da aplicação
COPY app.py .
COPY templates/ templates/

# Criar pastas necessárias
RUN mkdir -p uploads templates_word temp

# Expor porta
EXPOSE 8080

# Comando de inicialização
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 120 --log-level info 