#!/bin/bash

# Obter a porta do Railway ou usar padrão
PORT=${PORT:-8080}
echo "🚀 Starting on port: $PORT"

# Iniciar Gunicorn
exec gunicorn app_minimal:app \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 30 \
    --log-level debug 