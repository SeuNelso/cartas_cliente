# 🚂 Deploy no Railway - Configuração Simplificada

## 🎯 **Configuração Railway Simplificada**

### 📋 **Arquivos de Configuração:**

1. **railway.toml** - Configuração principal do Railway
2. **Dockerfile** - Build com Docker
3. **Procfile** - Comando de inicialização
4. **runtime.txt** - Versão do Python
5. **.dockerignore** - Otimização do build

### 🔧 **Configuração Atual:**

```toml
[build]
builder = "dockerfile"

[deploy]
startCommand = "gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120"
healthcheckPath = "/ping"
healthcheckTimeout = 300
```

### 🐳 **Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar pastas necessárias
RUN mkdir -p uploads templates_word temp

# Expor porta
EXPOSE 8080

# Comando de inicialização
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

### 📦 **Dependências:**

```txt
Flask==2.3.3
pandas==2.1.4
openpyxl==3.1.2
cairosvg==2.8.0
PyPDF2==3.0.1
Werkzeug==2.3.7
gunicorn==21.2.0
```

### 🚀 **Como Deployar:**

1. **Instalar Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Fazer login:**
   ```bash
   railway login
   ```

3. **Inicializar projeto:**
   ```bash
   railway init
   ```

4. **Deploy:**
   ```bash
   railway up
   ```

### 🎯 **Variáveis de Ambiente (Railway Dashboard):**

- `FLASK_ENV=production`
- `SECRET_KEY` (gerada automaticamente)
- `MAX_WORKERS=4`
- `MAX_CONTENT_LENGTH=52428800`

### ✅ **Vantagens desta Configuração:**

1. **Docker**: Build isolado e reproduzível
2. **Python 3.11**: Versão estável e compatível
3. **Workers limitados**: 1 worker para evitar problemas
4. **Timeout aumentado**: 120 segundos para processamento
5. **Healthcheck simples**: `/ping` para verificação

### 🎉 **Resultado Esperado:**

- ✅ Docker build sem problemas de ambiente
- ✅ pandas 2.1.4 funciona com Python 3.11
- ✅ Sem problemas de dependências do sistema
- ✅ Deploy rápido e estável

**Esta configuração simplificada deve resolver todos os problemas!** 🚂 