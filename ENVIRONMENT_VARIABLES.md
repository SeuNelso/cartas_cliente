# 🔧 Variáveis de Ambiente para Deploy

## 📋 Variáveis Necessárias

### 🔐 Configurações de Segurança
```bash
SECRET_KEY=sua_chave_secreta_aqui
```
- **Descrição**: Chave secreta para sessões Flask
- **Padrão**: `sua_chave_secreta_aqui`
- **Render.com**: Gerada automaticamente

### 🌍 Configurações do Flask
```bash
FLASK_ENV=production
```
- **Descrição**: Ambiente de execução
- **Valores**: `production`, `development`
- **Padrão**: `production`

### ⚙️ Configurações da Aplicação
```bash
MAX_WORKERS=4
```
- **Descrição**: Número máximo de workers para processamento
- **Padrão**: `4`
- **Range**: `1-10`

```bash
MAX_CONTENT_LENGTH=52428800
```
- **Descrição**: Tamanho máximo de upload (em bytes)
- **Padrão**: `52428800` (50MB)
- **Range**: `10485760-104857600` (10MB-100MB)

### 🚀 Configurações do Servidor
```bash
PORT=5000
```
- **Descrição**: Porta do servidor
- **Padrão**: `5000`
- **Render.com**: Definida automaticamente

## 🔧 Configuração no Render.com

### render.yaml
```yaml
services:
  - type: web
    name: carta-automatica
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT
    envVars:
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true
      - key: MAX_WORKERS
        value: 4
      - key: MAX_CONTENT_LENGTH
        value: 52428800
```

## 🎯 Variáveis Opcionais

### 🔍 Debug
```bash
DEBUG=false
```
- **Descrição**: Ativar modo debug
- **Padrão**: `false`
- **Desenvolvimento**: `true`

### 📊 Logs
```bash
LOG_LEVEL=INFO
```
- **Descrição**: Nível de logs
- **Valores**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Padrão**: `INFO` 