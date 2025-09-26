# 🚀 Sistema de Geração de PDFs - Aplicação Web

Sistema completo para geração automatizada de PDFs a partir de dados Excel usando templates Word.

## ✨ Características

- 🌐 **Interface Web Intuitiva** - Upload de arquivos e templates
- ⚡ **Performance** - 16 workers paralelos
- 📄 **Nomenclatura Inteligente** - `Carta_[NUMERO].pdf`
- 🔄 **Processamento Assíncrono** - Sem timeout
- 📊 **Progresso em Tempo Real** - Taxa de velocidade
- 🎨 **Templates Word** - Preservação de formatação
- 📦 **Download em ZIP** - Arquivos organizados

## 🚀 Início Rápido

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Iniciar Aplicação
```bash
python app.py
```

### 3. Acessar Aplicação
- 🌐 **URL Principal**: http://localhost:5000
- 🔗 **Health Check**: http://localhost:5000/api/health

## 📋 Como Usar

### 1. Upload de Template
- Acesse a aplicação web
- Faça upload de um arquivo `.docx` como template
- Use placeholders como `[NOME]`, `[NUMERO]`, `[ICCID]`

### 2. Upload de Dados
- Faça upload de um arquivo Excel (`.xlsx` ou `.xls`)
- Os dados serão processados automaticamente
- Visualize uma prévia dos dados

### 3. Gerar PDFs
- Selecione o template (opcional)
- Clique em "Gerar PDFs"
- Acompanhe o progresso em tempo real
- Baixe o ZIP com todos os PDFs

## ⚙️ Configurações

### Performance SUPER ULTRA
- **Workers**: 16 (máximo)
- **Chunk Size**: 5 registros
- **Timeout**: Nenhum (processa até terminar)
- **Arquivo**: 100MB máximo

### Resultados Esperados
- **74 PDFs**: 1-2 minutos
- **330 PDFs**: 5-8 minutos
- **Taxa**: 3-5 PDFs/segundo

## 🔧 API Endpoints

### Endpoints Principais
- `GET /` - Interface web
- `GET /api/health` - Verificação de saúde
- `POST /api/upload-template` - Upload de template
- `POST /api/upload` - Upload de dados Excel
- `POST /api/generate-pdf` - Gerar PDFs
- `GET /api/progress/<job_id>` - Verificar progresso
- `GET /api/download/<job_id>` - Download do resultado

## 📁 Estrutura de Arquivos

```
CARTA_AUTOMATICA/
├── app.py                    # Aplicação principal
├── templates/
│   └── index.html           # Interface web
├── templates_word/           # Templates Word
├── uploads/                  # Arquivos enviados
├── temp/                     # Arquivos temporários
├── logs/                     # Logs da aplicação
├── requirements.txt          # Dependências
└── README.md                # Documentação
```

## 🛠️ Tecnologias

- **Flask**: Framework web
- **ThreadPoolExecutor**: Processamento paralelo
- **python-docx**: Manipulação de Word
- **win32com**: Conversão Word para PDF
- **pandas**: Processamento de Excel
- **reportlab**: Geração de PDFs simples

## 🚀 Deploy

### Produção Local
```bash
python app.py
```

### Com Gunicorn (Linux)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

## 📞 Suporte

### Problemas Comuns
1. **Porta em uso**: Use porta diferente
2. **Arquivo muito grande**: Aumente limite
3. **Performance lenta**: Ajuste workers

### Logs
```bash
# Ver logs em tempo real
tail -f logs/app.log
```

---

**🎉 Sistema Limpo e Organizado!** 
