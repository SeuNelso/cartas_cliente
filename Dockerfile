FROM python:3.12.3-slim

WORKDIR /app

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app.py .
COPY start.sh .

# Tornar script executável
RUN chmod +x start.sh

# Expor porta
EXPOSE 8080

# Comando de inicialização
CMD ["./start.sh"] 