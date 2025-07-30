#!/bin/bash

echo "🚀 Iniciando aplicação..."

# Definir porta padrão se não estiver definida
if [ -z "$PORT" ]; then
    PORT=8080
    echo "⚠️  PORT não definida, usando porta padrão: $PORT"
else
    echo "✅ PORT definida: $PORT"
fi

echo "🌐 Iniciando gunicorn na porta $PORT..."

# Iniciar gunicorn
exec gunicorn app:app \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 120 \
    --log-level info 