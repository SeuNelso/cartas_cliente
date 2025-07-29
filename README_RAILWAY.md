# 🚂 Deploy no Railway

## 🎯 **Configuração Railway**

### 📋 **Arquivos de Configuração:**

1. **railway.json** - Configuração principal do Railway
2. **nixpacks.toml** - Configuração do builder NixPacks
3. **Procfile** - Comando de inicialização
4. **.railwayignore** - Arquivos ignorados no deploy

### 🔧 **Configuração Atual:**

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn app:app --bind 0.0.0.0:$PORT",
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
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

### ✅ **Vantagens do Railway:**

1. **NixPacks**: Builder mais inteligente
2. **Auto-detecção**: Detecta Python automaticamente
3. **Health checks**: Verificação automática de saúde
4. **Rollback**: Reversão fácil de deploys
5. **Logs**: Logs detalhados e em tempo real

### 🎉 **Resultado Esperado:**

- ✅ Railway escolhe Python disponível
- ✅ pandas 2.1.4 funciona automaticamente
- ✅ Sem problemas de versão
- ✅ Deploy rápido e estável

**O Railway deve funcionar melhor que o Render.com!** 🚂 