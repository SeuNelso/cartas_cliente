#!/bin/bash

echo "🚀 Iniciando build da aplicação no Render.com..."

# Verificar se estamos no ambiente correto
echo "📋 Verificando ambiente..."
python --version
pip --version

# Atualizar pip
echo "📦 Atualizando pip..."
pip install --upgrade pip setuptools wheel

# Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# Testar dependências individualmente
echo "✅ Testando dependências..."
python test_simple.py

# Verificar se as dependências foram instaladas corretamente
echo "✅ Verificando dependências..."
python -c "import flask; print(f'Flask {flask.__version__}')"
python -c "import pandas; print(f'pandas {pandas.__version__}')"
python -c "import openpyxl; print('openpyxl OK')"
python -c "from cairosvg import svg2pdf; print('cairosvg OK')"
python -c "from PyPDF2 import PdfMerger; print('PyPDF2 OK')"

echo "🎉 Build concluído com sucesso no Render.com!" 