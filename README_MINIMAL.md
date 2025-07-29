# 🚀 Deploy Mínimo no Railway

## 🎯 **Configuração Mínima**

### 📋 **Arquivos Mínimos:**

1. **app_minimal.py** - Aplicação Flask mínima
2. **requirements_minimal.txt** - Apenas Flask + Gunicorn
3. **Dockerfile** - Build mínimo
4. **railway.toml** - Configuração mínima
5. **Procfile** - Comando mínimo

### 🔧 **Aplicação Mínima:**

```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello World!"

@app.route('/health')
def health():
    return "OK"
```

### 📦 **Dependências Mínimas:**

```txt
Flask==2.3.3
gunicorn==21.2.0
```

### 🐳 **Dockerfile Mínimo:**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements_minimal.txt .
RUN pip install -r requirements_minimal.txt
COPY app_minimal.py .
EXPOSE 8080
CMD gunicorn app_minimal:app --bind 0.0.0.0:$PORT
```

### 🚀 **Como Deployar:**

1. **Faça commit** das mudanças
2. **Push para o repositório**
3. **Railway deve fazer deploy** automaticamente

### 🎯 **Teste:**

- ✅ `/` - Deve retornar "Hello World!"
- ✅ `/health` - Deve retornar "OK"

**Esta é a configuração mais simples possível que deve funcionar!** 🎯 