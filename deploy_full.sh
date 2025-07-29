#!/bin/bash

echo "🚀 Deployando versão completa do sistema de cartas automáticas..."

# Backup dos arquivos atuais
cp Dockerfile Dockerfile_minimal_backup
cp requirements_minimal.txt requirements_minimal_backup.txt
cp app_minimal.py app_minimal_backup.py

# Substituir pelos arquivos da versão completa
cp Dockerfile_full Dockerfile
cp requirements_full.txt requirements.txt
cp app_full.py app.py

echo "✅ Arquivos substituídos para versão completa"
echo "📦 Dependências incluídas:"
echo "   - Flask (web framework)"
echo "   - Pandas (Excel processing)"
echo "   - CairoSVG (SVG to PDF)"
echo "   - PyPDF2 (PDF merging)"
echo "   - OpenPyXL (Excel reading)"

echo "🚀 Faça commit e push para deployar a versão completa!" 