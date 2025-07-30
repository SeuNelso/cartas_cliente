FROM python:3.12.3-slim

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

# Limpar cache do pip
RUN pip cache purge

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir --force-reinstall -r requirements.txt

# Verificar que pandas NÃO está instalado
RUN python -c "import sys; assert 'pandas' not in sys.modules, 'pandas ainda está instalado!'; print('✅ pandas NÃO está instalado')"

# Copiar código da aplicação
COPY app.py .
COPY templates/ templates/
COPY start.sh .

# Criar pastas necessárias
RUN mkdir -p uploads templates_word temp

# Verificar se os templates foram copiados
RUN ls -la templates/

# Tornar script executável
RUN chmod +x start.sh

# Expor porta
EXPOSE 8080

# Comando de inicialização
CMD ["./start.sh"] 