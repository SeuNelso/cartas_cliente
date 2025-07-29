#!/bin/bash

echo "🚀 Iniciando build da aplicação..."

# Verificar se estamos no ambiente correto
echo "📋 Verificando ambiente..."
python --version
pip --version

# Instalar dependências
echo "📦 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# Verificar se as dependências foram instaladas corretamente
echo "✅ Verificando dependências..."
python -c "import flask; print(f'Flask {flask.__version__}')"
python -c "import pandas; print(f'pandas {pandas.__version__}')"
python -c "import openpyxl; print('openpyxl OK')"
python -c "from cairosvg import svg2pdf; print('cairosvg OK')"
python -c "from PyPDF2 import PdfMerger; print('PyPDF2 OK')"

echo "🎉 Build concluído com sucesso!" 