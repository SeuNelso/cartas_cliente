FROM python:3.11-slim

WORKDIR /app

# Definir variáveis de ambiente para forçar Python 3.11
ENV PYTHON_VERSION=3.11.7
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages

# Instalar dependências do sistema necessárias para cairosvg
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Atualizar pip e instalar dependências básicas
RUN pip install --upgrade pip setuptools wheel

# Instalar pandas primeiro (versão estável)
RUN pip install pandas==1.5.3

# Instalar outras dependências
RUN pip install Flask==2.3.3
RUN pip install openpyxl==3.1.2
RUN pip install cairosvg==2.8.0
RUN pip install PyPDF2==3.0.1
RUN pip install Werkzeug==2.3.7
RUN pip install gunicorn==21.2.0

# Verificar instalação
RUN python -c "import pandas; print(f'pandas {pandas.__version__} OK')"
RUN python -c "import flask; print(f'Flask {flask.__version__} OK')"
RUN python -c "from cairosvg import svg2pdf; print('cairosvg OK')"

# Copiar código da aplicação
COPY app.py .
COPY templates/ templates/

# Criar pastas necessárias
RUN mkdir -p uploads templates_word temp

# Expor porta
EXPOSE 8080

# Comando de inicialização
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 120 --log-level info 