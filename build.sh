#!/bin/bash

echo "🚀 Iniciando build da aplicação (versão sem pandas)..."
echo "📋 Verificando ambiente..."

# Verificar versão do Python
python --version

# Atualizar pip
pip install --upgrade pip setuptools wheel

# Instalar dependências sem pandas
echo "📦 Instalando dependências (sem pandas)..."
pip install Flask==2.3.3
pip install openpyxl==3.1.2
pip install cairosvg==2.8.0
pip install PyPDF2==3.0.1
pip install Werkzeug==2.3.7
pip install gunicorn==21.2.0

echo "✅ Verificando dependências..."
python -c "import flask; print(f'Flask {flask.__version__}')"
python -c "import openpyxl; print('openpyxl OK')"
python -c "from cairosvg import svg2pdf; print('cairosvg OK')"
python -c "from PyPDF2 import PdfMerger; print('PyPDF2 OK')"

echo "🎉 Build concluído com sucesso (sem pandas)!" 