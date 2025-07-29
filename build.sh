#!/bin/bash

echo "🚀 Iniciando build da aplicação..."
echo "📋 Verificando ambiente..."

# Verificar versão do Python
python --version

# Atualizar pip
pip install --upgrade pip setuptools wheel

# Instalar dependências do requirements.txt
echo "📦 Instalando dependências..."
pip install -r requirements.txt

echo "✅ Verificando dependências..."
python -c "import flask; print(f'Flask {flask.__version__}')"
python -c "import openpyxl; print('openpyxl OK')"
python -c "from cairosvg import svg2pdf; print('cairosvg OK')"
python -c "from PyPDF2 import PdfMerger; print('PyPDF2 OK')"

echo "🎉 Build concluído com sucesso!" 