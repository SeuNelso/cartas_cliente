#!/bin/bash

echo "🚀 Iniciando aplicação..."

# Criar pastas se não existirem
mkdir -p uploads temp

# Verificar templates
echo "📋 Verificando templates..."
ls -la templates/

echo "🌐 Iniciando gunicorn na porta $PORT..."

# Iniciar gunicorn
exec gunicorn app:app \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 120 \
    --log-level info \
    --preload 