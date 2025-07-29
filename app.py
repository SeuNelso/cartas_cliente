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

app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['MAX_WORKERS'] = int(os.environ.get('MAX_WORKERS', 3))
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB

# Pastas
UPLOAD_FOLDER = 'uploads'
TEMPLATE_FOLDER = 'templates_word'
TEMP_FOLDER = 'temp'

for folder in [UPLOAD_FOLDER, TEMPLATE_FOLDER, TEMP_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Jobs em andamento
jobs = {}

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

@app.route('/api/upload-template', methods=['POST'])
def upload_template():
    try:
        if 'template' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['template']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not file.filename.endswith('.svg'):
            return jsonify({'error': 'Apenas arquivos SVG são permitidos'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(TEMPLATE_FOLDER, filename)
        file.save(filepath)
        
        return jsonify({
            'message': 'Template SVG carregado com sucesso',
            'filename': filename
        })
    
    except Exception as e:
        return jsonify({'error': f'Erro ao processar template: {str(e)}'}), 500

@app.route('/api/generate-pdfs', methods=['POST'])
def generate_pdfs():
    try:
        data = request.get_json()
        excel_file = data.get('excel_file')
        template_file = data.get('template_file')
        selected_columns = data.get('selected_columns', [])
        
        if not excel_file or not template_file:
            return jsonify({'error': 'Arquivo Excel e template são obrigatórios'}), 400
        
        # Gerar ID único para o job
        job_id = str(uuid.uuid4())
        
        # Iniciar job em background
        thread = threading.Thread(
            target=process_pdf_generation,
            args=(job_id, excel_file, template_file, selected_columns)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Geração de PDFs iniciada',
            'job_id': job_id
        })
    
    except Exception as e:
        return jsonify({'error': f'Erro ao iniciar geração: {str(e)}'}), 500

def process_pdf_generation(job_id, excel_file, template_file, selected_columns):
    try:
        jobs[job_id] = {'status': 'processing', 'progress': 0, 'message': 'Iniciando processamento...'}
        
        # Ler dados do Excel usando openpyxl
        excel_path = os.path.join(UPLOAD_FOLDER, excel_file)
        columns, data = read_excel_with_openpyxl(excel_path)
        
        # Ler template SVG
        template_path = os.path.join(TEMPLATE_FOLDER, template_file)
        with open(template_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        jobs[job_id]['progress'] = 10
        jobs[job_id]['message'] = f'Processando {len(data)} registros...'
        
        # Lista para armazenar PDFs gerados
        pdf_files = []
        
        for index, row_data in enumerate(data):
            try:
                # Substituir placeholders no SVG usando a função melhorada
                current_svg = replace_placeholders(svg_content, row_data, selected_columns)
                
                # Gerar PDF temporário
                temp_svg = os.path.join(TEMP_FOLDER, f'temp_{index}.svg')
                temp_pdf = os.path.join(TEMP_FOLDER, f'temp_{index}.pdf')
                
                with open(temp_svg, 'w', encoding='utf-8') as f:
                    f.write(current_svg)
                
                # Converter SVG para PDF
                svg2pdf(url=temp_svg, write_to=temp_pdf)
                pdf_files.append(temp_pdf)
                
                # Atualizar progresso
                progress = 10 + int((index + 1) / len(data) * 80)
                jobs[job_id]['progress'] = progress
                jobs[job_id]['message'] = f'Processado {index + 1} de {len(data)} registros'
                
            except Exception as e:
                print(f"Erro ao processar linha {index}: {e}")
                continue
        
        # Mesclar PDFs
        jobs[job_id]['message'] = 'Mesclando PDFs...'
        merger = PdfMerger()
        
        for pdf_file in pdf_files:
            merger.append(pdf_file)
        
        # Salvar PDF final
        output_path = os.path.join(TEMP_FOLDER, f'output_{job_id}.pdf')
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
        jobs[job_id]['message'] = 'PDFs gerados com sucesso!'
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
    
    pdf_path = os.path.join(TEMP_FOLDER, f'output_{job_id}.pdf')
    if not os.path.exists(pdf_path):
        return jsonify({'error': 'Arquivo não encontrado'}), 404
    
    return send_file(pdf_path, as_attachment=True, download_name='cartas_geradas.pdf')

@app.route('/api/detect-placeholders', methods=['POST'])
def detect_placeholders():
    """Detecta automaticamente os placeholders em um template SVG"""
    try:
        if 'template_file' not in request.json:
            return jsonify({'error': 'Nome do template não fornecido'}), 400
        
        template_file = request.json['template_file']
        template_path = os.path.join(TEMPLATE_FOLDER, template_file)
        
        if not os.path.exists(template_path):
            return jsonify({'error': 'Template não encontrado'}), 404
        
        # Ler template SVG
        with open(template_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # Detectar todos os placeholders
        all_placeholders = set()
        
        # Padrões para detectar placeholders
        patterns = [
            r'\{\{([^}]+)\}\}',  # {{coluna}}
            r'\[([^\]]+)\]',      # [coluna]
            r'\{([^}]+)\}',       # {coluna}
            r'%([^%]+)%',         # %coluna%
            r'\$([^$]+)\$',       # $coluna$
            r'#([^#]+)#',         # #coluna#
            r'<tspan[^>]*>\s*([^<]+)\s*</tspan>',  # <tspan>coluna</tspan>
            r'<text[^>]*>\s*([^<]+)\s*</text>'     # <text>coluna</text>
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, svg_content)
            all_placeholders.update(matches)
        
        # Converter para lista e ordenar
        detected_placeholders = sorted(list(all_placeholders))
        
        return jsonify({
            'template_file': template_file,
            'detected_placeholders': detected_placeholders,
            'total_placeholders': len(detected_placeholders)
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao detectar placeholders: {str(e)}'}), 500

@app.route('/api/test-placeholders', methods=['POST'])
def test_placeholders():
    """Testa a detecção de placeholders em um template SVG"""
    try:
        if 'template_file' not in request.json:
            return jsonify({'error': 'Nome do template não fornecido'}), 400
        
        template_file = request.json['template_file']
        template_path = os.path.join(TEMPLATE_FOLDER, template_file)
        
        if not os.path.exists(template_path):
            return jsonify({'error': 'Template não encontrado'}), 404
        
        # Ler template SVG
        with open(template_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # Detectar diferentes tipos de placeholders
        detected_placeholders = {}
        
        # Padrões para detectar placeholders
        patterns = [
            (r'\{\{([^}]+)\}\}', '{{coluna}}'),
            (r'\[([^\]]+)\]', '[coluna]'),
            (r'\{([^}]+)\}', '{coluna}'),
            (r'%([^%]+)%', '%coluna%'),
            (r'\$([^$]+)\$', '$coluna$'),
            (r'#([^#]+)#', '#coluna#'),
            (r'<tspan[^>]*>\s*([^<]+)\s*</tspan>', '<tspan>coluna</tspan>'),
            (r'<text[^>]*>\s*([^<]+)\s*</text>', '<text>coluna</text>')
        ]
        
        for pattern, format_name in patterns:
            matches = re.findall(pattern, svg_content)
            if matches:
                detected_placeholders[format_name] = list(set(matches))
        
        return jsonify({
            'template_file': template_file,
            'detected_placeholders': detected_placeholders,
            'total_placeholders': sum(len(placeholders) for placeholders in detected_placeholders.values())
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao testar placeholders: {str(e)}'}), 500

# ===== NOVA FUNCIONALIDADE: PROCESSAMENTO DE EXCEL COM MÚLTIPLOS NÚMEROS =====

def processar_excel_multiplos_numeros(caminho_arquivo: str):
    """
    Processa arquivo Excel com múltiplos números por cliente
    """
    try:
        # Ler arquivo Excel
        headers, data = read_excel_with_openpyxl(caminho_arquivo)
        
        # Verificar se tem as colunas necessárias
        colunas_necessarias = ['Cliente', 'Número', 'ICCID']
        for coluna in colunas_necessarias:
            if coluna not in headers:
                raise ValueError(f"Coluna '{coluna}' não encontrada no Excel")
        
        # Agrupar por cliente
        clientes = {}
        for row in data:
            cliente = row['Cliente']
            if cliente not in clientes:
                clientes[cliente] = []
            
            clientes[cliente].append({
                'numero': str(row['Número']),
                'iccid': str(row['ICCID'])
            })
        
        # Gerar cartas para cada cliente
        cartas_geradas = []
        max_numeros_por_carta = 6
        
        for cliente, numeros in clientes.items():
            # Dividir em grupos de 6 números
            grupos = []
            for i in range(0, len(numeros), max_numeros_por_carta):
                grupos.append(numeros[i:i + max_numeros_por_carta])
            
            for i, grupo in enumerate(grupos):
                carta = {
                    'cliente': cliente,
                    'numeros': grupo,
                    'numero_carta': i + 1,
                    'total_cartas': len(grupos)
                }
                cartas_geradas.append(carta)
        
        return cartas_geradas
        
    except Exception as e:
        raise Exception(f"Erro ao processar Excel: {str(e)}")

def gerar_svg_carta_multiplos_numeros(dados_carta: dict, template_path: str):
    """
    Gera SVG da carta substituindo placeholders para múltiplos números
    """
    try:
        # Ler template SVG
        with open(template_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # Preencher números e ICCIDs
        svg_modificado = svg_content
        
        for i, numero_data in enumerate(dados_carta['numeros'], 1):
            svg_modificado = svg_modificado.replace(
                f'{{{{NUMERO_{i}}}}}', numero_data['numero']
            )
            svg_modificado = svg_modificado.replace(
                f'{{{{ICCID_{i}}}}}', numero_data['iccid']
            )
        
        # Remover linhas vazias (placeholders não preenchidos)
        svg_modificado = remover_linhas_vazias_svg(svg_modificado)
        
        return svg_modificado
        
    except Exception as e:
        raise Exception(f"Erro ao gerar SVG: {str(e)}")

def remover_linhas_vazias_svg(svg_content: str):
    """
    Remove linhas que contêm placeholders vazios
    """
    # Padrão para encontrar elementos text com placeholders
    padrao_numero = r'<text[^>]*>\s*<tspan[^>]*>\s*\{\{NUMERO_\d+\}\}\s*</tspan>\s*</text>'
    padrao_iccid = r'<text[^>]*>\s*<tspan[^>]*>\s*\{\{ICCID_\d+\}\}\s*</tspan>\s*</text>'
    
    # Remover elementos com placeholders não preenchidos
    svg_content = re.sub(padrao_numero, '', svg_content)
    svg_content = re.sub(padrao_iccid, '', svg_content)
    
    return svg_content

@app.route('/api/processar-excel-multiplos', methods=['POST'])
def processar_excel_multiplos():
    """
    Nova rota para processar Excel com múltiplos números por cliente
    """
    try:
        if 'excel_file' not in request.json:
            return jsonify({'error': 'Nome do arquivo Excel não fornecido'}), 400
        
        excel_file = request.json['excel_file']
        excel_path = os.path.join(UPLOAD_FOLDER, excel_file)
        
        if not os.path.exists(excel_path):
            return jsonify({'error': 'Arquivo Excel não encontrado'}), 404
        
        # Processar Excel
        cartas = processar_excel_multiplos_numeros(excel_path)
        
        return jsonify({
            'success': True,
            'total_cartas': len(cartas),
            'cartas': cartas,
            'message': f'Processamento concluído! {len(cartas)} cartas serão geradas.'
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao processar Excel: {str(e)}'}), 500

@app.route('/api/gerar-cartas-multiplos', methods=['POST'])
def gerar_cartas_multiplos():
    """
    Gera cartas SVG com múltiplos números por cliente
    """
    try:
        if 'excel_file' not in request.json:
            return jsonify({'error': 'Nome do arquivo Excel não fornecido'}), 400
        
        excel_file = request.json['excel_file']
        excel_path = os.path.join(UPLOAD_FOLDER, excel_file)
        
        if not os.path.exists(excel_path):
            return jsonify({'error': 'Arquivo Excel não encontrado'}), 404
        
        # Processar Excel
        cartas = processar_excel_multiplos_numeros(excel_path)
        
        # Template SVG
        template_path = os.path.join(TEMPLATE_FOLDER, 'carta-digi-6linhas.svg')
        if not os.path.exists(template_path):
            return jsonify({'error': 'Template SVG não encontrado'}), 404
        
        # Gerar cartas SVG
        cartas_svg = []
        for carta in cartas:
            svg_content = gerar_svg_carta_multiplos_numeros(carta, template_path)
            cartas_svg.append({
                'cliente': carta['cliente'],
                'numero_carta': carta['numero_carta'],
                'total_cartas': carta['total_cartas'],
                'svg_content': svg_content
            })
        
        return jsonify({
            'success': True,
            'total_cartas': len(cartas_svg),
            'cartas': cartas_svg,
            'message': f'Geração concluída! {len(cartas_svg)} cartas SVG criadas.'
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar cartas: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 