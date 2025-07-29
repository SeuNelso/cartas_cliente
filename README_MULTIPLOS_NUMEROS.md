# Funcionalidade: Múltiplos Números por Cliente

Esta nova funcionalidade permite processar arquivos Excel com múltiplos números por cliente e gerar cartas personalizadas automaticamente.

## 🎯 Como Funciona

### 1. **Estrutura do Excel**
O arquivo Excel deve ter as seguintes colunas:
- **Cliente**: Nome do cliente
- **Número**: Número de telemóvel
- **ICCID**: Código ICCID do cartão SIM

### 2. **Processamento Inteligente**
- **Agrupa por cliente**: Todos os números do mesmo cliente ficam juntos
- **Limite de 6 números**: Máximo 6 números por carta
- **Divisão automática**: Se um cliente tiver mais de 6 números, cria múltiplas cartas

### 3. **Template Dinâmico**
- **Um template para todos**: Template SVG com 6 linhas predefinidas
- **Remoção automática**: Linhas vazias são removidas automaticamente
- **Design consistente**: Mantém a qualidade visual original

## 📋 Exemplo de Excel

| Cliente | Número | ICCID |
|---------|--------|-------|
| João Silva | 928307037 | 8935102241115578094 |
| João Silva | 928351767 | 8935102241115578102 |
| João Silva | 928351768 | 8935102241115578103 |
| Maria Costa | 928351769 | 8935102241115578104 |
| Maria Costa | 928351770 | 8935102241115578105 |
| Maria Costa | 928351771 | 8935102241115578106 |
| Maria Costa | 928351772 | 8935102241115578107 |
| Maria Costa | 928351773 | 8935102241115578108 |
| Maria Costa | 928351774 | 8935102241115578109 |

## 🔄 Resultado

### Para João Silva (3 números):
- **1 carta** com todos os 3 números na mesma tabela

### Para Maria Costa (6 números):
- **1 carta** com todos os 6 números na mesma tabela

### Para um cliente com 8 números:
- **1ª carta**: números 1-6
- **2ª carta**: números 7-8

## 🚀 Como Usar

### 1. **Via API (Recomendado)**

```bash
# Processar Excel
curl -X POST http://localhost:5000/api/processar-excel-multiplos \
  -H "Content-Type: application/json" \
  -d '{"excel_file": "dados_clientes.xlsx"}'

# Gerar cartas SVG
curl -X POST http://localhost:5000/api/gerar-cartas-multiplos \
  -H "Content-Type: application/json" \
  -d '{"excel_file": "dados_clientes.xlsx"}'
```

### 2. **Via Script Python**

```python
from processador_excel import ProcessadorExcel

# Criar processador
processador = ProcessadorExcel()

# Processar Excel
cartas = processador.processar_excel("dados_clientes.xlsx")

# Salvar cartas
processador.salvar_cartas(cartas, "cartas_geradas")
```

### 3. **Via Script de Teste**

```bash
python teste_multiplos_numeros.py
```

## 📁 Arquivos Criados

### Template SVG
- `templates_word/carta-digi-6linhas.svg` - Template com 6 linhas

### Scripts
- `processador_excel.py` - Processador principal
- `teste_multiplos_numeros.py` - Script de teste
- `exemplo_dados.xlsx` - Arquivo de exemplo

### APIs Adicionadas
- `/api/processar-excel-multiplos` - Processa Excel
- `/api/gerar-cartas-multiplos` - Gera cartas SVG

## ⚙️ Configurações

### Máximo de Números por Carta
```python
# Em processador_excel.py
self.max_numeros_por_carta = 6  # Alterar conforme necessário
```

### Placeholders do Template
```xml
<!-- No template SVG -->
{{NUMERO_1}} {{ICCID_1}}
{{NUMERO_2}} {{ICCID_2}}
{{NUMERO_3}} {{ICCID_3}}
{{NUMERO_4}} {{ICCID_4}}
{{NUMERO_5}} {{ICCID_5}}
{{NUMERO_6}} {{ICCID_6}}
```

## 🎨 Vantagens

✅ **Automatização completa** - Processa qualquer quantidade de dados
✅ **Flexibilidade** - Funciona com 1 ou 100 números por cliente
✅ **Limite controlado** - Máximo 6 números por carta
✅ **Design consistente** - Mantém qualidade visual
✅ **Performance otimizada** - Processamento eficiente
✅ **Fácil manutenção** - Um template para todos os casos

## 🔧 Troubleshooting

### Erro: "Coluna 'Cliente' não encontrada"
- Verifique se o Excel tem as colunas: `Cliente`, `Número`, `ICCID`
- Os nomes das colunas devem ser exatos

### Erro: "Template SVG não encontrado"
- Verifique se o arquivo `carta-digi-6linhas.svg` existe em `templates_word/`

### Cartas com linhas vazias
- O sistema remove automaticamente linhas não utilizadas
- Se aparecerem linhas vazias, verifique o template SVG

## 📞 Suporte

Para dúvidas ou problemas, verifique:
1. Estrutura do arquivo Excel
2. Template SVG
3. Logs da aplicação
4. Script de teste

---

**Desenvolvido para CARTA_AUTOMATICA** 🚀 