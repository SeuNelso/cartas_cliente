FROM python:3.11-slim

WORKDIR /app

COPY requirements_minimal.txt .
RUN pip install -r requirements_minimal.txt

COPY app_minimal.py .
COPY start.sh .

# Tornar o script executável
RUN chmod +x start.sh

EXPOSE 8080

# Usar o script de inicialização
CMD ["./start.sh"] 