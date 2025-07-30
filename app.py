from flask import Flask, request, jsonify, render_template, send_file
import openpyxl
import os
import uuid
import threading
import re
from werkzeug.utils import secure_filename
from cairosvg import svg2pdf
from PyPDF2 import PdfMerger
import tempfile
from collections import defaultdict

app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['MAX_WORKERS'] = int(os.environ.get('MAX_WORKERS', 3))
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB

# Pastas
UPLOAD_FOLDER = 'uploads'
TEMPLATE_FOLDER = 'templates'
TEMP_FOLDER = 'temp'

for folder in [UPLOAD_FOLDER, TEMPLATE_FOLDER, TEMP_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Jobs em andamento
jobs = {}

def selecionar_template(quantidade_numeros):
    """
    Seleciona o template SVG apropriado baseado na quantidade de números
    """
    if quantidade_numeros == 1:
        return "carta_1_numero.svg"
    elif quantidade_numeros <= 6:
        return f"carta_{quantidade_numeros}_numeros.svg"
    else:
        # Para mais de 6 números, usar template de 6
        return "carta_6_numeros.svg"

def agrupar_por_cliente(data, coluna_cliente):
    """
    Agrupa os dados por cliente
    """
    clientes = defaultdict(list)
    
    for row in data:
        cliente = row.get(coluna_cliente, 'Cliente Desconhecido')
        clientes[cliente].append(row)
    
    return clientes

def dividir_numeros_por_carta(numeros, max_por_carta=6):
    """
    Divide números em grupos para múltiplas cartas se necessário
    """
    grupos = []
    for i in range(0, len(numeros), max_por_carta):
        grupos.append(numeros[i:i + max_por_carta])
    return grupos

def read_excel_with_openpyxl(filepath):
    """Lê arquivo Excel usando openpyxl em vez de pandas"""
    workbook = openpyxl.load_workbook(filepath)
    sheet = workbook.active
    
    # Obter cabeçalhos (primeira linha)
    headers = []
    for cell in sheet[1]:
        if cell.value:
            headers.append(str(cell.value))
    
    # Obter dados
    data = []
    for row in sheet.iter_rows(min_row=2):
        row_data = {}
        for i, cell in enumerate(row):
            if i < len(headers):
                row_data[headers[i]] = cell.value
        if any(row_data.values()):  # Só adicionar se a linha não estiver vazia
            data.append(row_data)
    
    return headers, data

def replace_placeholders(svg_content, row_data, selected_columns):
    """
    Substitui placeholders no SVG usando diferentes formatos
    """
    current_svg = svg_content
    
    for column in selected_columns:
        if column not in row_data or row_data[column] is None:
            value = ''
        else:
            value = str(row_data[column])
        
        # Diferentes formatos de placeholder
        placeholders = [
            f'{{{{{column}}}}}',  # {{coluna}}
            f'[{column}]',        # [coluna]
            f'{{{column}}}',      # {coluna}
            f'%{column}%',        # %coluna%
            f'${column}$',        # $coluna$
            f'#{column}#',        # #coluna#
        ]
        
        # Substituir cada formato
        for placeholder in placeholders:
            current_svg = current_svg.replace(placeholder, value)
        
        # Também procurar por placeholders em tags tspan
        # Padrão: <tspan>coluna</tspan> ou <tspan x="..." y="...">coluna</tspan>
        tspan_pattern = rf'<tspan[^>]*>\s*{re.escape(column)}\s*</tspan>'
        current_svg = re.sub(tspan_pattern, f'<tspan>{value}</tspan>', current_svg)
        
        # Procurar por placeholders em elementos text
        text_pattern = rf'<text[^>]*>\s*{re.escape(column)}\s*</text>'
        current_svg = re.sub(text_pattern, f'<text>{value}</text>', current_svg)
    
    return current_svg

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    return "OK"

@app.route('/ping')
def ping():
    return "pong"

@app.route('/debug')
def debug():
    try:
        import os
        import glob
        info = {
            'status': 'OK',
            'port': os.environ.get('PORT', '5000'),
            'templates_folder': TEMPLATE_FOLDER,
            'uploads_folder': UPLOAD_FOLDER,
            'temp_folder': TEMP_FOLDER,
            'templates_count': len(glob.glob(f"{TEMPLATE_FOLDER}/*.svg")),
            'templates': [os.path.basename(f) for f in glob.glob(f"{TEMPLATE_FOLDER}/*.svg")]
        }
        return jsonify(info)
    except Exception as e:
        return jsonify({'status': 'ERROR', 'message': str(e)}), 500

@app.route('/api/upload-excel', methods=['POST'])
def upload_excel():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Apenas arquivos Excel são permitidos'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Ler dados do Excel usando openpyxl
        columns, data = read_excel_with_openpyxl(filepath)
        
        return jsonify({
            'message': 'Arquivo Excel carregado com sucesso',
            'filename': filename,
            'columns': columns,
            'rows': len(data)
        })
    
    except Exception as e:
        return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500

@app.route('/api/generate-pdfs-por-cliente', methods=['POST'])
def generate_pdfs_por_cliente():
    try:
        data = request.get_json()
        excel_file = data.get('excel_file')
        coluna_cliente = data.get('coluna_cliente', 'Cliente')
        coluna_numero = data.get('coluna_numero', 'Número')
        coluna_iccid = data.get('coluna_iccid', 'ICCID')
        
        if not excel_file:
            return jsonify({'error': 'Arquivo Excel é obrigatório'}), 400
        
        # Gerar ID único para o job
        job_id = str(uuid.uuid4())
        
        # Iniciar job em background
        thread = threading.Thread(
            target=process_pdf_generation_por_cliente,
            args=(job_id, excel_file, coluna_cliente, coluna_numero, coluna_iccid)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Geração de PDFs por cliente iniciada',
            'job_id': job_id
        })
    
    except Exception as e:
        return jsonify({'error': f'Erro ao iniciar geração: {str(e)}'}), 500

def process_pdf_generation_por_cliente(job_id, excel_file, coluna_cliente, coluna_numero, coluna_iccid):
    try:
        jobs[job_id] = {'status': 'processing', 'progress': 0, 'message': 'Iniciando processamento por cliente...'}
        
        # Ler dados do Excel
        excel_path = os.path.join(UPLOAD_FOLDER, excel_file)
        columns, data = read_excel_with_openpyxl(excel_path)
        
        # Agrupar dados por cliente
        clientes = agrupar_por_cliente(data, coluna_cliente)
        
        jobs[job_id]['progress'] = 10
        jobs[job_id]['message'] = f'Processando {len(clientes)} clientes...'
        
        # Lista para armazenar PDFs gerados
        pdf_files = []
        total_cartas = 0
        
        for cliente_nome, registros_cliente in clientes.items():
            try:
                # Extrair números e ICCIDs do cliente
                numeros_cliente = []
                for registro in registros_cliente:
                    numero = registro.get(coluna_numero, '')
                    iccid = registro.get(coluna_iccid, '')
                    if numero and iccid:
                        numeros_cliente.append({
                            'numero': str(numero),
                            'iccid': str(iccid)
                        })
                
                if not numeros_cliente:
                    continue
                
                # Dividir números em grupos de 6 se necessário
                grupos_numeros = dividir_numeros_por_carta(numeros_cliente, 6)
                
                for grupo in grupos_numeros:
                    # Selecionar template baseado na quantidade
                    quantidade = len(grupo)
                    template_file = selecionar_template(quantidade)
                    template_path = os.path.join(TEMPLATE_FOLDER, template_file)
                    
                    if not os.path.exists(template_path):
                        print(f"Template não encontrado: {template_file}")
                        continue
                    
                    # Ler template SVG
                    with open(template_path, 'r', encoding='utf-8') as f:
                        svg_content = f.read()
                    
                    # Substituir dados do cliente
                    svg_modificado = svg_content
                    
                    # Substituir nome do cliente
                    svg_modificado = svg_modificado.replace('{{CLIENTE}}', cliente_nome)
                    svg_modificado = svg_modificado.replace('[CLIENTE]', cliente_nome)
                    svg_modificado = svg_modificado.replace('{CLIENTE}', cliente_nome)
                    svg_modificado = svg_modificado.replace('%CLIENTE%', cliente_nome)
                    svg_modificado = svg_modificado.replace('$CLIENTE$', cliente_nome)
                    svg_modificado = svg_modificado.replace('#CLIENTE#', cliente_nome)
                    
                    # Substituir números e ICCIDs
                    if len(grupo) == 1:
                        # Para template com 1 número, usar placeholders simples
                        numero = grupo[0]['numero']
                        iccid = grupo[0]['iccid']
                        
                        svg_modificado = svg_modificado.replace('[NUMERO]', numero)
                        svg_modificado = svg_modificado.replace('{NUMERO}', numero)
                        svg_modificado = svg_modificado.replace('{{NUMERO}}', numero)
                        svg_modificado = svg_modificado.replace('%NUMERO%', numero)
                        svg_modificado = svg_modificado.replace('$NUMERO$', numero)
                        svg_modificado = svg_modificado.replace('#NUMERO#', numero)
                        
                        svg_modificado = svg_modificado.replace('[ICCID]', iccid)
                        svg_modificado = svg_modificado.replace('{ICCID}', iccid)
                        svg_modificado = svg_modificado.replace('{{ICCID}}', iccid)
                        svg_modificado = svg_modificado.replace('%ICCID%', iccid)
                        svg_modificado = svg_modificado.replace('$ICCID$', iccid)
                        svg_modificado = svg_modificado.replace('#ICCID#', iccid)
                    else:
                        # Para templates com múltiplos números, substituir sequencialmente
                        for i, item in enumerate(grupo):
                            numero = item['numero']
                            iccid = item['iccid']
                            
                            # Substituir o primeiro [NUMERO] e [ICCID] encontrados
                            svg_modificado = svg_modificado.replace('[NUMERO]', numero, 1)
                            svg_modificado = svg_modificado.replace('{NUMERO}', numero, 1)
                            svg_modificado = svg_modificado.replace('{{NUMERO}}', numero, 1)
                            svg_modificado = svg_modificado.replace('%NUMERO%', numero, 1)
                            svg_modificado = svg_modificado.replace('$NUMERO$', numero, 1)
                            svg_modificado = svg_modificado.replace('#NUMERO#', numero, 1)
                            
                            svg_modificado = svg_modificado.replace('[ICCID]', iccid, 1)
                            svg_modificado = svg_modificado.replace('{ICCID}', iccid, 1)
                            svg_modificado = svg_modificado.replace('{{ICCID}}', iccid, 1)
                            svg_modificado = svg_modificado.replace('%ICCID%', iccid, 1)
                            svg_modificado = svg_modificado.replace('$ICCID$', iccid, 1)
                            svg_modificado = svg_modificado.replace('#ICCID#', iccid, 1)
                    
                    # Limpar placeholders não utilizados apenas para múltiplos números
                    if len(grupo) > 1:
                        for i in range(quantidade + 1, 7):  # Limpar placeholders de 7 a 6
                            svg_modificado = svg_modificado.replace(f'{{NUMERO_{i}}}', '')
                            svg_modificado = svg_modificado.replace(f'[NUMERO_{i}]', '')
                            svg_modificado = svg_modificado.replace(f'{{NUMERO{i}}}', '')
                            svg_modificado = svg_modificado.replace(f'%NUMERO_{i}%', '')
                            svg_modificado = svg_modificado.replace(f'$NUMERO_{i}$', '')
                            svg_modificado = svg_modificado.replace(f'#NUMERO_{i}#', '')
                            
                            svg_modificado = svg_modificado.replace(f'{{ICCID_{i}}}', '')
                            svg_modificado = svg_modificado.replace(f'[ICCID_{i}]', '')
                            svg_modificado = svg_modificado.replace(f'{{ICCID{i}}}', '')
                            svg_modificado = svg_modificado.replace(f'%ICCID_{i}%', '')
                            svg_modificado = svg_modificado.replace(f'$ICCID_{i}$', '')
                            svg_modificado = svg_modificado.replace(f'#ICCID_{i}#', '')
                    
                    # Gerar PDF temporário
                    temp_svg = os.path.join(TEMP_FOLDER, f'temp_cliente_{total_cartas}.svg')
                    temp_pdf = os.path.join(TEMP_FOLDER, f'temp_cliente_{total_cartas}.pdf')
                    
                    with open(temp_svg, 'w', encoding='utf-8') as f:
                        f.write(svg_modificado)
                    
                    print(f"Gerando PDF para cliente {cliente_nome} com {len(grupo)} números")
                    print(f"Template usado: {template_file}")
                    print(f"SVG salvo em: {temp_svg}")
                    
                    # Converter SVG para PDF
                    try:
                        svg2pdf(url=temp_svg, write_to=temp_pdf)
                        print(f"PDF gerado com sucesso: {temp_pdf}")
                        pdf_files.append(temp_pdf)
                        total_cartas += 1
                    except Exception as e:
                        print(f"Erro ao converter SVG para PDF: {e}")
                        continue
                
                # Atualizar progresso
                progress = 10 + int((len(pdf_files) / (len(clientes) * 2)) * 80)  # Estimativa
                jobs[job_id]['progress'] = min(progress, 90)
                jobs[job_id]['message'] = f'Processado cliente: {cliente_nome} ({len(grupos_numeros)} cartas)'
                
            except Exception as e:
                print(f"Erro ao processar cliente {cliente_nome}: {e}")
                continue
        
        # Mesclar PDFs
        jobs[job_id]['message'] = 'Mesclando PDFs...'
        merger = PdfMerger()
        
        for pdf_file in pdf_files:
            merger.append(pdf_file)
        
        # Salvar PDF final
        output_path = os.path.join(TEMP_FOLDER, f'output_cliente_{job_id}.pdf')
        merger.write(output_path)
        merger.close()
        
        # Limpar arquivos temporários
        for pdf_file in pdf_files:
            try:
                os.remove(pdf_file)
            except:
                pass
        
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = 100
        jobs[job_id]['message'] = f'PDFs gerados com sucesso! Total: {total_cartas} cartas'
        jobs[job_id]['download_url'] = f'/api/download/{job_id}'
        
    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['message'] = f'Erro: {str(e)}'

@app.route('/api/job-status/<job_id>')
def job_status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job não encontrado'}), 404
    
    return jsonify(jobs[job_id])

@app.route('/api/download/<job_id>')
def download_pdf(job_id):
    if job_id not in jobs or jobs[job_id]['status'] != 'completed':
        return jsonify({'error': 'PDF não disponível'}), 404
    
    # Tentar ambos os formatos de arquivo
    pdf_path_normal = os.path.join(TEMP_FOLDER, f'output_{job_id}.pdf')
    pdf_path_cliente = os.path.join(TEMP_FOLDER, f'output_cliente_{job_id}.pdf')
    
    if os.path.exists(pdf_path_normal):
        return send_file(pdf_path_normal, as_attachment=True, download_name='cartas_geradas.pdf')
    elif os.path.exists(pdf_path_cliente):
        return send_file(pdf_path_cliente, as_attachment=True, download_name='cartas_por_cliente.pdf')
    else:
        return jsonify({'error': 'Arquivo não encontrado'}), 404

@app.route('/api/detect-excel-columns', methods=['POST'])
def detect_excel_columns():
    """Detecta colunas do Excel e sugere mapeamento para cliente, número e ICCID"""
    try:
        if 'excel_file' not in request.json:
            return jsonify({'error': 'Nome do arquivo Excel não fornecido'}), 400
        
        excel_file = request.json['excel_file']
        excel_path = os.path.join(UPLOAD_FOLDER, excel_file)
        
        if not os.path.exists(excel_path):
            return jsonify({'error': 'Arquivo Excel não encontrado'}), 404
        
        # Ler dados do Excel
        columns, data = read_excel_with_openpyxl(excel_path)
        
        # Sugerir mapeamento baseado em palavras-chave
        sugestoes = {
            'cliente': [],
            'numero': [],
            'iccid': []
        }
        
        for coluna in columns:
            coluna_lower = coluna.lower()
            
            # Detectar coluna de cliente
            if any(palavra in coluna_lower for palavra in ['cliente', 'nome', 'name', 'customer']):
                sugestoes['cliente'].append(coluna)
            
            # Detectar coluna de número
            if any(palavra in coluna_lower for palavra in ['numero', 'number', 'num', 'telefone', 'phone']):
                sugestoes['numero'].append(coluna)
            
            # Detectar coluna de ICCID
            if any(palavra in coluna_lower for palavra in ['iccid', 'sim', 'card']):
                sugestoes['iccid'].append(coluna)
        
        return jsonify({
            'excel_file': excel_file,
            'columns': columns,
            'total_rows': len(data),
            'sugestoes': sugestoes
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao detectar colunas: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting Flask app on port {port}")
    print(f"📁 Templates folder: {TEMPLATE_FOLDER}")
    print(f"📁 Uploads folder: {UPLOAD_FOLDER}")
    print(f"📁 Temp folder: {TEMP_FOLDER}")
    
    # Verificar se os templates existem
    import glob
    templates = glob.glob(f"{TEMPLATE_FOLDER}/*.svg")
    print(f"📋 Templates encontrados: {len(templates)}")
    for template in templates:
        print(f"  - {os.path.basename(template)}")
    
    app.run(host='0.0.0.0', port=port) 