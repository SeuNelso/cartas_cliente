#!/bin/bash

echo "🚀 Iniciando aplicação..."

# Verificar se as pastas existem
echo "📁 Verificando pastas..."
if [ ! -d "templates" ]; then
    echo "❌ Pasta templates não encontrada!"
    exit 1
fi

if [ ! -d "uploads" ]; then
    echo "📁 Criando pasta uploads..."
    mkdir -p uploads
fi

if [ ! -d "temp" ]; then
    echo "📁 Criando pasta temp..."
    mkdir -p temp
fi

# Verificar templates
echo "📋 Verificando templates..."
TEMPLATES_COUNT=$(ls templates/*.svg 2>/dev/null | wc -l)
echo "✅ Encontrados $TEMPLATES_COUNT templates"

if [ $TEMPLATES_COUNT -eq 0 ]; then
    echo "❌ Nenhum template encontrado!"
    exit 1
fi

# Listar templates
echo "📋 Templates disponíveis:"
ls -la templates/*.svg

echo "✅ Aplicação pronta para iniciar!"
echo "🌐 Iniciando gunicorn na porta $PORT..."

# Iniciar gunicorn
exec gunicorn app:app \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 120 \
    --log-level info \
    --preload \
    --max-requests 1000 \
    --max-requests-jitter 100 