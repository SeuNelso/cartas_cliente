#!/bin/bash

# Script de build para Render com Python 3.13.4
echo "🚀 Iniciando build no Render com Python 3.13.4..."

# Verificar versão do Python
echo "🐍 Versão do Python:"
python --version

# Instalar dependências do sistema necessárias para cairosvg
echo "📦 Instalando dependências do sistema..."
apt-get update && apt-get install -y \
    gcc \
    g++ \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Atualizar pip para versão mais recente
echo "🔄 Atualizando pip..."
pip install --upgrade pip setuptools wheel

# Instalar dependências Python uma por uma para evitar conflitos
echo "🐍 Instalando dependências Python..."
pip install --no-cache-dir --constraint constraints.txt Flask==3.0.0
pip install --no-cache-dir --constraint constraints.txt Werkzeug==3.0.1
pip install --no-cache-dir --constraint constraints.txt openpyxl==3.1.2
pip install --no-cache-dir --constraint constraints.txt cairosvg==2.8.0
pip install --no-cache-dir --constraint constraints.txt PyPDF2==3.0.1
pip install --no-cache-dir --constraint constraints.txt gunicorn==21.2.0

# Verificar instalação
echo "✅ Verificando instalação..."
python -c "import flask; print(f'✅ Flask {flask.__version__} instalado')"
python -c "import cairosvg; print('✅ cairosvg instalado com sucesso')"
python -c "import openpyxl; print('✅ openpyxl instalado com sucesso')"
python -c "import PyPDF2; print('✅ PyPDF2 instalado com sucesso')"

echo "🎉 Build concluído com sucesso!" 